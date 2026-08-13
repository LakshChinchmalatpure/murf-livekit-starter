import json
import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db
import schemes
from prompt import SYSTEM_PROMPT

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Global dict to track session success states
active_calls_status = {}

def _get_room(session):
    if not session:
        return None
    if hasattr(session, "room"):
        return session.room
    if hasattr(session, "room_io") and hasattr(session.room_io, "room"):
        return session.room_io.room
    return None

# # Change this prompt to change what your voice agent does.
# # See README.md for example prompts (customer support, language tutor, receptionist).
# SYSTEM_PROMPT = """You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate. Your responses are concise and without complex formatting, emojis, or symbols."""


class Assistant(Agent):
    def __init__(self, instructions: str = SYSTEM_PROMPT) -> None:
        # Instruct LLM to call confirm_documents_delivered when appropriate
        tool_instruction = "\n\n- When you have answered the caller's questions, completed an eligibility check, or listed the required documents, you MUST call the tool confirm_documents_delivered."
        super().__init__(instructions=instructions + tool_instruction)

    @function_tool
    async def confirm_documents_delivered(self, context: RunContext) -> str:
        """Mark that the caller has successfully received the document list or completed their eligibility check.

        Call this tool as soon as you have provided the user with the list of documents they need,
        or after they complete their eligibility check.
        """
        logger.info("confirm_documents_delivered tool called.")
        try:
            room = _get_room(context.session)
            if room:
                try:
                    room_sid = await room.sid
                except TypeError:
                    room_sid = room.sid
                if not room_sid:
                    room_sid = room.name
                if room_sid:
                    active_calls_status[room_sid] = True
        except Exception as e:
            logger.error(f"Error in confirm_documents_delivered: {e}")
        return "Success status recorded."

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
            if (
                context.session
                and context.session.room_io
                and context.session.room_io.linked_participant
            ):
                user_id = context.session.room_io.linked_participant.identity
        except (RuntimeError, AttributeError):
            pass

        logger.info(
            f"lookup_caller called with name={name}, connection user_id={user_id}"
        )

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
        self, context: RunContext, name: str, language_preference: str, facts: str
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
            if (
                context.session
                and context.session.room_io
                and context.session.room_io.linked_participant
            ):
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
            return json.dumps(
                {
                    "error": "Failed to retrieve schemes list due to an internal error.",
                    "is_live": False,
                    "last_updated": "unknown",
                }
            )

    @function_tool
    async def check_scheme_eligibility(
        self, context: RunContext, scheme_name: str, answers: str
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
        logger.info(
            f"check_scheme_eligibility tool called for scheme_name={scheme_name} with answers={answers}"
        )
        try:
            answers_dict = json.loads(answers)
        except Exception:
            return json.dumps(
                {
                    "error": "Invalid input format. Answers must be a valid JSON string.",
                    "is_live": False,
                    "last_updated": "unknown",
                }
            )

        try:
            res = schemes.evaluate_eligibility(scheme_name, answers_dict)
            try:
                room = _get_room(context.session)
                if room:
                    try:
                        room_sid = await room.sid
                    except TypeError:
                        room_sid = room.sid
                    if not room_sid:
                        room_sid = room.name
                    if room_sid:
                        active_calls_status[room_sid] = True
            except Exception as e:
                logger.error(f"Error updating success status in check_scheme_eligibility: {e}")
            return json.dumps(res)
        except Exception as e:
            logger.error(f"Error in check_scheme_eligibility: {e}")
            return json.dumps(
                {
                    "error": "Failed to evaluate scheme eligibility due to an internal error.",
                    "is_live": False,
                    "last_updated": "unknown",
                }
            )


    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        name: str,
        what_happened: str,
        checked: str,
        urgency: str,
        language: str,
        follow_up: str,
    ) -> str:
        """Create an escalation ticket for a human agent when the caller reports fraud or needs a decision the agent cannot make.

        Before calling this tool, you MUST explicitly ask the caller for permission to share their details.

        Args:
            name: The name of the caller needing help.
            what_happened: A brief summary of what happened or what decision is needed. Do NOT include sensitive info like full bank account numbers, credit/debit card numbers, PINs, OTPs, CVVs, passwords.
            checked: What the agent already checked (e.g. eligibility criteria, basic fraud checks).
            urgency: Urgency level of the request (must be one of 'High', 'Medium', 'Low').
            language: The caller's language (e.g. 'English', 'Hindi', 'Hinglish').
            follow_up: Preferred follow-up method (e.g. 'Call', 'Email').
        """
        logger.info(f"create_escalation tool called for user={name}")
        try:
            res = db.save_escalation(
                name=name,
                what_happened=what_happened,
                checked=checked,
                urgency=urgency,
                language=language,
                follow_up=follow_up
            )
            return json.dumps({"status": "success", "reference_id": res["reference_id"]})
        except Exception as e:
            logger.error(f"Error in create_escalation: {e}")
            return json.dumps({"error": "Failed to create escalation ticket due to an internal error."})


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="en-IN-abhinav",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

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

    # Join the room first so we receive participant events!
    await ctx.connect()

    # Wait for the user to join the room
    logger.info("Waiting for participant to join...")
    user = await ctx.wait_for_participant()
    logger.info(f"Participant joined: identity={user.identity}, kind={user.kind}")

    # Wait for SIP call to be answered/active if it is a SIP participant
    if user.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        import asyncio

        logger.info("Waiting for SIP call to be answered (sip.callStatus == active)...")
        for _ in range(60):
            status = user.attributes.get("sip.callStatus")
            logger.info(f"Current SIP call status: {status}")
            if status == "active":
                break
            await asyncio.sleep(0.5)

    # Query the caller database using the participant's identity
    record = db.get_caller(user_id=user.identity)
    logger.info(f"Caller database lookup for '{user.identity}': {record}")

    # Default instructions & setup
    is_outbound = (
        ctx.job.metadata == "outbound"
        or user.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
    )

    try:
        room_sid = await ctx.room.sid
    except TypeError:
        room_sid = ctx.room.sid
    if not room_sid:
        room_sid = ctx.room.name
    caller_id = user.identity
    caller_name = user.name or "Caller"
    if record and record.get("name"):
        caller_name = record["name"]

    db.start_call(
        call_id=room_sid,
        caller_id=caller_id,
        caller_name=caller_name,
        call_type="outbound" if is_outbound else "inbound"
    )

    active_calls_status[room_sid] = False

    try:
        greeting = None
        if is_outbound:
            name = "there"
            scheme_name = "your registered government scheme"
            documents_list = "- Relevant eligibility documents"

            if record:
                name = record.get("name", "there")
                facts = record.get("facts", {})
                schemes_checked = facts.get("schemes_checked", [])
                eligible = facts.get("eligible", "undetermined")

                if schemes_checked and eligible == "yes":
                    scheme_name = schemes_checked[0]
                    try:
                        scheme_details = (
                            schemes.fetch_schemes_data()[0]
                            .get("schemes", {})
                            .get(scheme_name, {})
                        )
                        docs = scheme_details.get("documents", [])
                        if docs:
                            documents_list = "\n".join([f"- {d}" for d in docs])
                    except Exception as e:
                        logger.error(f"Error fetching scheme details: {e}")

            # Custom system prompt for outbound call with deadline
            instructions = f"""You are a professional, polite, and helpful voice assistant for the Government Schemes service.
You are making an outbound call to {name} regarding the {scheme_name} scheme.
The user was previously found eligible for {scheme_name} on their last interaction.
The application deadline for {scheme_name} is approaching on August 15, 2026.
Your goal is to help {name} complete their application, check if they need help with the next steps, and verify they have the required documents.

Required documents for {scheme_name}:
{documents_list}

Rules for the call:
1. In the first two sentences of the conversation, you must state: who is calling, why, and how to stop.
   (Example: "Hello {name}, this is the Government Schemes Assistant calling to remind you that the application deadline is approaching for the {scheme_name} scheme, for which you were previously found eligible. If you want this call to stop, just say 'stop' or hang up at any time.")
2. Maintain a friendly, helpful, and professional tone.
3. Keep your responses concise (1-2 sentences) and suitable for a phone call. Avoid markdown, lists, emojis, or complex formatting.
4. If the user says 'stop', 'stop calling', or expresses that they want to end the call, politely say goodbye and hang up.
"""
            greeting = f"Hello {name}, this is the Government Schemes Assistant calling to remind you that the application deadline is approaching for the {scheme_name} scheme, for which you were previously found eligible. If you want this call to stop, just say 'stop' or hang up at any time."

            # Update the agent with the new instructions
            session.update_agent(Assistant(instructions=instructions))

        # Greet the user if this is an outbound call
        if greeting:
            logger.info("Greeting outbound caller...")
            await session.say(greeting, allow_interruptions=True)
            # Mark outbound call as successful once greeted/documents delivered
            active_calls_status[room_sid] = True

        # Keep the session block alive until the room is disconnected
        import asyncio
        while ctx.room.connection_state != rtc.ConnectionState.CONN_DISCONNECTED:
            await asyncio.sleep(1)

    finally:
        # Retrieve outcome status and update db
        is_success = active_calls_status.pop(room_sid, False)
        db.complete_call(call_id=room_sid, status="success" if is_success else "failed")


if __name__ == "__main__":
    cli.run_app(server)
