import asyncio
import logging
import os
import time

from dotenv import load_dotenv
from livekit import api

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("outbound")

# Load environment variables from backend/.env.local
load_dotenv(".env.local")


async def main():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    # Support spelling variants from backend/.env.local
    sip_uri = os.getenv("LINPHON_SIP_URI") or os.getenv("LINPHONE_SIP_URI")
    trunk_id = os.getenv("LIVEKIT_SIP_TRUNCK_ID") or os.getenv("LIVEKIT_SIP_TRUNK_ID")

    if not url or not api_key or not api_secret:
        logger.error(
            "Error: LiveKit credentials (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) must be set in environment."
        )
        return

    if not sip_uri:
        logger.error("Error: LINPHON_SIP_URI is not set in environment.")
        return

    if not trunk_id:
        logger.error("Error: LIVEKIT_SIP_TRUNCK_ID is not set in environment.")
        return

    logger.info(f"Initializing LiveKit API with URL: {url}")
    lk_api = api.LiveKitAPI(url=url, api_key=api_key, api_secret=api_secret)

    # Use a specific room name for the outbound session
    room_name = f"outbound_call_laksh_{int(time.time())}"

    # 1. Create agent dispatch
    logger.info(
        f"Creating agent dispatch for room '{room_name}' for agent 'my-agent'..."
    )
    try:
        dispatch = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="my-agent", room=room_name, metadata="outbound"
            )
        )
        logger.info(f"Agent dispatch created successfully. Dispatch ID: {dispatch.id}")
    except Exception as e:
        logger.error(f"Failed to create agent dispatch: {e}")
        logger.info("Continuing call setup...")

    # Extract SIP user/username from SIP URI if needed (LiveKit API expects a SIP user/phone number)
    sip_to = sip_uri
    if sip_to.startswith("sip:"):
        sip_to = sip_to[4:]
    if "@" in sip_to:
        sip_to = sip_to.split("@")[0]

    # 2. Initiate outbound SIP Call
    logger.info(
        f"Initiating outbound SIP call to user '{sip_to}' (URI: '{sip_uri}') using trunk '{trunk_id}'..."
    )
    try:
        # Create SIP participant to dial the user and add them to the room
        participant = await lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=sip_to,
                room_name=room_name,
                participant_identity="voice_assistant_user_7335",  # Target eligible user in DB
                participant_name="Laksh",
                wait_until_answered=True,
            )
        )
        logger.info(
            f"SIP Outbound call placed! Participant ID: {participant.participant_id}, Call ID: {participant.sip_call_id}"
        )
    except Exception as e:
        logger.error(f"Failed to initiate outbound SIP call: {e}")
    finally:
        await lk_api.aclose()
        logger.info("LiveKit API connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
