import asyncio
import threading
from voice_player import VoiceImagePlayer, edge_speak
from speech_to_text import record_voice
#from recognition import record_voice
from groq_ai import get_response

async def get_voice_input():
    return await asyncio.to_thread(record_voice)

async def ai_loop(player):

    while True:
        user_text = await get_voice_input()
        if not user_text:
            continue

        print("User:", user_text)
        lowered = user_text.lower().strip()

        if lowered in ["exit", "quit", "goodbye", "bye", "stop","mute"]:
            edge_speak("Goodbye sir.", player)
            player.root.after(300, player.root.destroy)
            break

        response = get_response(user_text)
        print("AI:", response)

        edge_speak(response, player)

        player.write_log(f"You: {user_text}")
        player.write_log(f"AI: {response}")


def main_loop():
    print("")

    player = VoiceImagePlayer("face.png", size=(900, 900))

    def thread_target():
        asyncio.run(ai_loop(player))

    threading.Thread(target=thread_target, daemon=True).start()
    player.root.mainloop()

if __name__ == "__main__":
    main_loop()