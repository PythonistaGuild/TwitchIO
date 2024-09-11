import asyncio
from twitchio.ext import commands, sounds


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token="TOKEN", prefix="!", initial_channels=["CHANNEL"])
        self.audio_manager = sounds.AudioQueueManager()
        self.song_dict = {
            "song_one": "C:\\PATH\\TO\\FILE.mp3",
            "song_two": "C:\\PATH\\TO\\FILE.mp3",
            "song_three": "C:\\PATH\\TO\\FILE.mp3",
        }

    async def event_ready(self):
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.audio_manager.queue_loop())

    @commands.command(name="sr")
    async def addsound(self, ctx: commands.Context, sound: str):
        sound_path = self.song_dict[sound]
        await self.audio_manager.add_audio(sound_path)
        await ctx.send(f"Added sound to queue: {sound_path}")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        await ctx.send(f"Skipped the current sound. {self.audio_manager.current_sound}")
        self.audio_manager.skip_audio()

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        self.audio_manager.pause_audio()

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        self.audio_manager.resume_audio()

    @commands.command(name="queue")
    async def queue(self, ctx: commands.Context):
        queue_contents = self.audio_manager.get_queue_contents()
        await ctx.send(f"Queue contents: {queue_contents}")

    async def close(self):
        self.task.cancel()
        await super().close()


if __name__ == "__main__":
    bot = Bot()
    bot.run()
