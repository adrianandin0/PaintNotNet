import sys
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter, QColor

from core.selection import SelectionEngine

def test_all_cases():
    print("Running SelectionEngine verification test suite...")

    # Case 1: All 8 handles after flip horizontal
    engine = SelectionEngine()
    engine.set_rectangle(QRectF(100, 100, 200, 100)) # W=200, H=100, center=(200, 150)
    img = QImage(200, 100, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.red)
    engine.init_raw_image(img)
    engine.original_image_pos = QPointF(100, 100)

    engine.flip_floating_image(horizontal=True)

    handles = engine.get_handles()
    # Check physical positions of each handle
    expected_positions = {
        engine.HANDLE_TOP_LEFT: (100.0, 100.0),
        engine.HANDLE_TOP_RIGHT: (300.0, 100.0),
        engine.HANDLE_BOTTOM_LEFT: (100.0, 200.0),
        engine.HANDLE_BOTTOM_RIGHT: (300.0, 200.0),
        engine.HANDLE_TOP_CENTER: (200.0, 100.0),
        engine.HANDLE_BOTTOM_CENTER: (200.0, 200.0),
        engine.HANDLE_MIDDLE_LEFT: (100.0, 150.0),
        engine.HANDLE_MIDDLE_RIGHT: (300.0, 150.0),
    }

    for hid, (exp_x, exp_y) in expected_positions.items():
        center = handles[hid].center()
        assert abs(center.x() - exp_x) < 0.5, f"Handle {hid} x mismatch: {center.x()} != {exp_x}"
        assert abs(center.y() - exp_y) < 0.5, f"Handle {hid} y mismatch: {center.y()} != {exp_y}"
        hit = engine.hit_test(center)
        assert hit == hid, f"Hit test at handle {hid} returned {hit}"

    print("PASS: Case 1 - Handles correctly mapped after horizontal flip.")

    # Case 2: All 8 handles after flip vertical
    engine = SelectionEngine()
    engine.set_rectangle(QRectF(100, 100, 200, 100))
    engine.init_raw_image(img)
    engine.original_image_pos = QPointF(100, 100)

    engine.flip_floating_image(horizontal=False, vertical=True)
    handles = engine.get_handles()
    for hid, (exp_x, exp_y) in expected_positions.items():
        center = handles[hid].center()
        assert abs(center.x() - exp_x) < 0.5
        assert abs(center.y() - exp_y) < 0.5
        hit = engine.hit_test(center)
        assert hit == hid

    print("PASS: Case 2 - Handles correctly mapped after vertical flip.")

    # Case 3: Rotation (90, 180, 270)
    for rot in [90, 180, 270]:
        engine = SelectionEngine()
        engine.set_rectangle(QRectF(100, 100, 200, 100))
        engine.init_raw_image(img)
        engine.original_image_pos = QPointF(100, 100)
        engine.rotate_floating_image(rot)

        img_center = engine.original_image_pos + QPointF(engine.floating_image.width() / 2.0, engine.floating_image.height() / 2.0)
        path_center = engine.active_rect.center()
        assert abs(img_center.x() - path_center.x()) < 1.0, f"Rot {rot}: img_center x != path_center x"
        assert abs(img_center.y() - path_center.y()) < 1.0, f"Rot {rot}: img_center y != path_center y"

        handles = engine.get_handles()
        for hid, r in handles.items():
            hit = engine.hit_test(r.center())
            assert hit == hid, f"Rot {rot}: hit test at handle {hid} returned {hit}"

    print("PASS: Case 3 - Rotations 90, 180, 270 keep image and path aligned.")

    # Case 4: Move then flip then resize
    engine = SelectionEngine()
    engine.set_rectangle(QRectF(100, 100, 200, 100))
    engine.init_raw_image(img)
    engine.original_image_pos = QPointF(100, 100)

    # Move by (50, 75)
    engine.begin_transform(QPointF(200, 150), Qt.MouseButton.LeftButton, engine.HANDLE_MOVE)
    engine.update_transform(QPointF(250, 225))
    engine.end_transform()
    assert engine.original_image_pos == QPointF(150, 175)
    assert engine.active_rect.topLeft() == QPointF(150, 175)

    # Flip horizontal
    engine.flip_floating_image(horizontal=True)
    assert engine.original_image_pos == QPointF(150, 175)
    assert engine.active_rect.topLeft() == QPointF(150, 175)

    # Resize from bottom-right (350, 275) to (390, 315)
    hit = engine.hit_test(QPointF(350, 275))
    assert hit == engine.HANDLE_BOTTOM_RIGHT
    engine.begin_transform(QPointF(350, 275), Qt.MouseButton.LeftButton, hit)
    engine.update_transform(QPointF(390, 315))
    engine.end_transform()

    assert abs(engine.original_image_pos.x() - 150.0) < 1e-3
    assert abs(engine.original_image_pos.y() - 175.0) < 1e-3
    assert abs(engine.active_rect.x() - 150.0) < 1e-3
    assert abs(engine.active_rect.y() - 175.0) < 1e-3
    assert abs(engine.active_rect.width() - 240.0) < 1e-3
    assert abs(engine.active_rect.height() - 140.0) < 1e-3
    assert engine.floating_image.width() == 240
    assert engine.floating_image.height() == 140

    print("PASS: Case 4 - Move, flip, and resize maintain exact alignment.")

    # Case 5: Selection without floating image (MoveSelectOnlyTool)
    engine = SelectionEngine()
    engine.set_rectangle(QRectF(100, 100, 200, 100))
    assert engine.floating_image is None
    handles = engine.get_handles()
    assert len(handles) == 8
    assert handles[engine.HANDLE_TOP_LEFT].center() == QPointF(100, 100)
    assert handles[engine.HANDLE_BOTTOM_RIGHT].center() == QPointF(300, 200)

    hit = engine.hit_test(QPointF(300, 200))
    assert hit == engine.HANDLE_BOTTOM_RIGHT
    engine.begin_transform(QPointF(300, 200), Qt.MouseButton.LeftButton, hit)
    engine.update_transform(QPointF(350, 250))
    engine.end_transform()
    assert engine.active_rect.width() == 250.0
    assert engine.active_rect.height() == 150.0

    print("PASS: Case 5 - MoveSelectOnlyTool without floating image works properly.")

    print("\nALL TEST CASES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all_cases()
