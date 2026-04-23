from conftest import load_skill_module


page_planner = load_skill_module("page_planner")


def test_page_planner_builds_page_plan_with_blocks():
    plan = page_planner.build_page_plan(
        page_number=1,
        width_px=1000,
        height_px=1500,
        background_path="page.png",
        text_items=[
            {
                "text": "Hello",
                "left": 0,
                "top": 0,
                "width": 10,
                "height": 10,
                "font_size": 12,
                "color": "#000000",
                "alignment": "left",
                "confidence": 0.9,
            }
        ],
        image_items=[
            {
                "path": "img.png",
                "left": 0,
                "top": 0,
                "width": 10,
                "height": 10,
                "confidence": 0.9,
                "extractable": True,
            }
        ],
    )
    assert len(plan.text_blocks) == 1
    assert len(plan.image_blocks) == 1
