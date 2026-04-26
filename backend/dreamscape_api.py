"""
backend/dreamscape_api.py
Run from DreamScape root:
    uvicorn backend.dreamscape_api:app --reload --port 8000
"""
import sys, os, uuid, asyncio, threading
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
for p in [_here, _root]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="DreamScape API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

stories:    dict = {}
progress:   dict = {}
ws_clients: dict = {}


class StoryRequest(BaseModel):
    prompt: str
    rounds: int = 3


def sync_broadcast(story_id: str, phase: str, status: str, detail: str = ""):
    msg = {"phase": phase, "status": status, "detail": detail}
    if story_id not in progress:
        progress[story_id] = []
    progress[story_id].append(msg)


def run_pipeline(story_id: str, prompt: str, rounds: int):
    try:
        from agents.plot_agent          import PlotAgent
        from agents.character_agent     import CharacterAgent
        from agents.emotion_agent       import EmotionAgent
        from agents.visual_agent        import VisualAgent
        from agents.audio_agent         import AudioAgent
        from coordinator.round_manager  import RoundManager
        from memory.story_state         import StoryState
        from memory.character_profiles  import CharacterProfileStore
        from memory.world_bible         import WorldBible
        from scene.pipeline             import ScenePipeline
        from generation.image_gen       import ImageGenerator
        from generation.video_gen       import VideoGenerator
        from generation.tts_gen         import TTSGenerator
        from generation.music_gen       import MusicGenerator
        from assembly.audio_mixer       import AudioMixer
        from assembly.video_assembler   import VideoAssembler
        from config                     import get_settings

        settings = get_settings()
        stories[story_id] = {"status": "running", "prompt": prompt}

        sync_broadcast(story_id, "story", "running", "Generating story with 6 agents...")
        story_state        = StoryState(initial_prompt=prompt)
        character_profiles = CharacterProfileStore()
        world_bible        = WorldBible()
        agents = [PlotAgent(), CharacterAgent(), EmotionAgent(), VisualAgent(), AudioAgent()]
        manager = RoundManager(agents=agents, story_state=story_state,
            character_profiles=character_profiles, world_bible=world_bible, total_rounds=rounds)
        manager.run_all_rounds()
        full_story = story_state.get_full_story()
        stories[story_id]["story"] = full_story
        sync_broadcast(story_id, "story", "complete", full_story[:300] + "...")

        sync_broadcast(story_id, "scenes", "running", "Structuring scenes...")
        pipeline   = ScenePipeline()
        scene_list = pipeline.run(story_text=full_story, story_id=story_id,
                                   character_profiles=character_profiles.get_all())
        stories[story_id]["scenes"] = scene_list.total_scenes
        sync_broadcast(story_id, "scenes", "complete", f"{scene_list.total_scenes} scenes structured")

        sync_broadcast(story_id, "images", "running", "Generating images (Pollinations.AI)...")
        img_gen     = ImageGenerator()
        image_paths = {}
        if img_gen.check_comfyui_running():
            image_paths = img_gen.generate_for_all_scenes(scene_list.scenes)
            for scene in scene_list.scenes:
                path = image_paths.get(scene.sequence_number)
                if path:
                    scene.image_path = path
        sync_broadcast(story_id, "images", "complete",
                       f"{sum(1 for v in image_paths.values() if v)} images generated")

        sync_broadcast(story_id, "audio", "running", "Generating TTS narration...")
        tts_gen     = TTSGenerator()
        tts_results = tts_gen.generate_for_all_scenes(scene_list.scenes)
        sync_broadcast(story_id, "audio", "running", "Generating background music...")
        music_gen   = MusicGenerator(model_size="small")
        music_paths = music_gen.generate_for_all_scenes(scene_list.scenes)
        sync_broadcast(story_id, "audio", "running", "Mixing audio...")
        mixer       = AudioMixer()
        mixed_audio = mixer.mix_all_scenes(story_id, tts_results, music_paths)
        for scene_num, path in mixed_audio.items():
            scene = next((s for s in scene_list.scenes if s.sequence_number == scene_num), None)
            if scene and path:
                scene.audio_path = path
        sync_broadcast(story_id, "audio", "complete", "Audio generation complete")

        clip_paths = {}
        if settings.magic_hour_api_key:
            sync_broadcast(story_id, "video_clips", "running", "Animating with Magic Hour...")
            scenes_with_images = [s for s in scene_list.scenes if image_paths.get(s.sequence_number)]
            if scenes_with_images:
                video_gen  = VideoGenerator()
                clip_paths = video_gen.generate_clips_for_all_scenes(scenes_with_images, image_paths)
                success    = sum(1 for v in clip_paths.values() if v)
                sync_broadcast(story_id, "video_clips", "complete", f"{success} clips animated")
        else:
            sync_broadcast(story_id, "video_clips", "skipped", "Using Ken Burns effect")

        sync_broadcast(story_id, "assembly", "running", "Assembling final video...")
        assembler   = VideoAssembler()
        scene_paths = assembler.assemble_all_scenes(scene_list.scenes, mixed_audio, clip_paths=clip_paths)
        final_video = assembler.stitch_final_video(story_id, scene_paths)
        stories[story_id]["video_path"] = final_video
        stories[story_id]["status"]     = "complete"
        sync_broadcast(story_id, "assembly", "complete", f"Video ready: {os.path.basename(final_video)}")
        sync_broadcast(story_id, "done", "complete", story_id)

    except Exception as e:
        import traceback
        stories[story_id]["status"] = "failed"
        stories[story_id]["error"]  = str(e)
        sync_broadcast(story_id, "error", "failed", f"{str(e)}\n{traceback.format_exc()[-500:]}")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "DreamScape API"}


@app.post("/api/story")
async def create_story(req: StoryRequest, background_tasks: BackgroundTasks):
    story_id = f"story_{uuid.uuid4().hex[:8]}"
    stories[story_id]  = {"status": "queued", "prompt": req.prompt}
    progress[story_id] = []
    background_tasks.add_task(
        lambda: threading.Thread(
            target=run_pipeline,
            args=(story_id, req.prompt, req.rounds),
            daemon=True
        ).start()
    )
    return {"story_id": story_id, "status": "queued"}


@app.get("/api/story/{story_id}")
async def get_story(story_id: str):
    if story_id not in stories:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return {**stories[story_id], "story_id": story_id,
            "progress": progress.get(story_id, [])}


@app.get("/api/story/{story_id}/video")
async def get_video(story_id: str):
    story      = stories.get(story_id, {})
    video_path = story.get("video_path")
    if not video_path or not os.path.exists(video_path):
        return JSONResponse({"error": "Video not ready"}, status_code=404)
    return FileResponse(video_path, media_type="video/mp4",
                        filename=f"{story_id}_final.mp4")


@app.get("/api/gallery")
async def get_gallery():
    completed = [
        {"story_id": sid, "prompt": d.get("prompt",""),
         "story": d.get("story","")[:200], "scenes": d.get("scenes",0),
         "has_video": bool(d.get("video_path"))}
        for sid, d in stories.items()
        if d.get("status") == "complete"
    ]
    return {"stories": completed}


@app.websocket("/ws/{story_id}")
async def websocket_endpoint(websocket: WebSocket, story_id: str):
    await websocket.accept()
    if story_id not in ws_clients:
        ws_clients[story_id] = []
    ws_clients[story_id].append(websocket)

    for msg in progress.get(story_id, []):
        await websocket.send_json(msg)

    last_sent = len(progress.get(story_id, []))
    try:
        while True:
            await asyncio.sleep(0.5)
            msgs = progress.get(story_id, [])
            for msg in msgs[last_sent:]:
                await websocket.send_json(msg)
            last_sent = len(msgs)
            if stories.get(story_id, {}).get("status") in ("complete", "failed"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        if story_id in ws_clients and websocket in ws_clients[story_id]:
            ws_clients[story_id].remove(websocket)
