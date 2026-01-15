import os
from src.pipeline.ocr_stage import OCRStage
from src.pipeline.refine_stage import RefineStage
from src.pipeline.resume_manager import ResumeManager
from src.logging.run_state import RunState

# Example config (replace with actual config loading)
config = {
    "log_dir": "logs/run_2026-01-15_17-35",
    "ocr_mode": "local",  # or "ai"
    "ocr_engine": "easyocr",
    "llm_refinement": False,
    "api_key": None,
    "num_pages": 3
}

os.makedirs(config["log_dir"], exist_ok=True)

resume_mgr = ResumeManager(config["log_dir"])
run_state = RunState(config["log_dir"])

start_page = 1
if resume_mgr.has_incomplete_run():
    if resume_mgr.prompt_resume():
        last = resume_mgr.get_last_completed_page()
        if last:
            start_page = last + 1

ocr_stage = OCRStage(config["log_dir"], config["ocr_mode"], config["ocr_engine"])
refine_stage = RefineStage(api_key=config["api_key"], enabled=config["llm_refinement"])

for page_index in range(start_page, config["num_pages"] + 1):
    try:
        # Replace None with actual image loading logic
        ocr_result = ocr_stage.run_ocr(page_index, image=None)
        run_state.update(last_completed_page=page_index)
        text = ocr_result["structured_text"]
        if config["llm_refinement"] and config["api_key"]:
            text = refine_stage.refine(text)
        # TODO: Add structuring and markdown composition here
    except Exception as e:
        run_state.update(error=str(e))
        break
