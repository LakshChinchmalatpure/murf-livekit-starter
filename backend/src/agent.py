import logging

from dotenv import load_dotenv
from prompt import SYSTEM_PROMPT
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    function_tool,
    RunContext,
)
import json
import db
import schemes
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# # Change this prompt to change what your voice agent does.
# # See README.md for example prompts (customer support, language tutor, receptionist).
# SYSTEM_PROMPT = """You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate. Your responses are concise and without complex formatting, emojis, or symbols."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_caller(self, context: RunContext, name: str | None = None) -> str:
        """Look up a caller's record in the database.
        
        This tool can automatically search using the current call's connection ID.
        If the caller provides a name, you can also search by name.
        
        Args:
            name: Optional name of the caller to search for.
        """
        user_id = None
        try:
            if context.session and context.session.room_io and context.session.room_io.linked_participant:
                user_id = context.session.room_io.linked_participant.identity
        except (RuntimeError, AttributeError):
            pass
            
        logger.info(f"lookup_caller called with name={name}, connection user_id={user_id}")
        
        # 1. Try to find by connection user_id
        record = None
        if user_id:
            record = db.get_caller(user_id=user_id)
            
        # 2. If not found and name is provided, try to find by name
        if not record and name:
            record = db.get_caller(name=name)
            
        if record:
            logger.info(f"lookup_caller found record: {record}")
            return json.dumps(record)
            
        logger.info("lookup_caller: No record found.")
        return "No caller record found."

    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: str
    ) -> str:
        """Save or update a caller's record in the database.
        
        IMPORTANT: Before calling this tool, you MUST explicitly ask the caller for permission 
        to remember/save their information and tell them what you are saving. 
        If they refuse, do NOT call this tool.
        
        Args:
            name: The caller's name.
            language_preference: The caller's preferred language (e.g. 'English', 'Hindi', 'Hinglish').
            facts: A JSON string containing 2 to 4 facts relevant to their Financial Services track 
                   (e.g., {"schemes_checked": ["PM Kisan"], "eligible": "yes"}). 
                   Do NOT include any account numbers, PINs, OTPs, CVVs, card numbers, or ID numbers here.
        """
        user_id = None
        try:
            if context.session and context.session.room_io and context.session.room_io.linked_participant:
                user_id = context.session.room_io.linked_participant.identity
        except (RuntimeError, AttributeError):
            pass
            
        if not user_id:
            # Fallback to name as user_id if participant identity is not available
            user_id = f"user_{name.lower().replace(' ', '_')}"
            
        logger.info(f"save_caller_info called for user_id={user_id}, name={name}")
        
        try:
            facts_dict = json.loads(facts)
        except Exception:
            return "Error: facts must be a valid JSON string."
            
        record = db.save_caller(user_id, name, language_preference, facts_dict)
        return f"Caller record saved successfully: {json.dumps(record)}"

    @function_tool
    async def get_supported_schemes(self, context: RunContext) -> str:
        """Get the list of supported Indian government financial schemes and their descriptions.
        
        Use this tool when a user asks what schemes you support, or what schemes they can check eligibility for.
        """
        logger.info("get_supported_schemes tool called.")
        try:
            res = schemes.get_supported_schemes_list()
            return json.dumps(res)
        except Exception as e:
            logger.error(f"Error in get_supported_schemes: {e}")
            return json.dumps({
                "error": "Failed to retrieve schemes list due to an internal error.",
                "is_live": False,
                "last_updated": "unknown"
            })

    @function_tool
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        scheme_name: str,
        answers: str
    ) -> str:
        """Evaluate a user's eligibility and retrieve the required document checklist for a specific scheme.
        
        Before calling this tool, you must gather the relevant answers (e.g. age, monthly income, land ownership) 
        from the user through conversation.
        
        Args:
            scheme_name: The exact key of the scheme to check (e.g., 'PM Kisan', 'PM Jan Dhan Yojana', 'PM Shram Yogi Maandhan', 'PM Suraksha Bima Yojana').
            answers: A JSON string containing the user's details.
                     Required keys for 'PM Kisan': {"owns_land": bool, "is_income_tax_payer": bool}
                     Required keys for 'PM Jan Dhan Yojana': {"has_other_bank_account": bool, "age": int}
                     Required keys for 'PM Shram Yogi Maandhan': {"age": int, "monthly_income": float, "is_unorganized_worker": bool, "is_covered_under_epf_esic": bool, "is_income_tax_payer": bool}
                     Required keys for 'PM Suraksha Bima Yojana': {"age": int, "has_savings_bank_account": bool}
        """
        logger.info(f"check_scheme_eligibility tool called for scheme_name={scheme_name} with answers={answers}")
        try:
            answers_dict = json.loads(answers)
        except Exception:
            return json.dumps({
                "error": "Invalid input format. Answers must be a valid JSON string.",
                "is_live": False,
                "last_updated": "unknown"
            })
            
        try:
            res = schemes.evaluate_eligibility(scheme_name, answers_dict)
            return json.dumps(res)
        except Exception as e:
            logger.error(f"Error in check_scheme_eligibility: {e}")
            return json.dumps({
                "error": "Failed to evaluate scheme eligibility due to an internal error.",
                "is_live": False,
                "last_updated": "unknown"
            })


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="en-IN-abhinav", 
                locale="en-IN",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
