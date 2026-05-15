import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_language_keyboard_has_two_buttons():
    from keyboards import language_keyboard
    kb = language_keyboard()
    all_buttons = [btn.text for row in kb.keyboard for btn in row]
    assert "\U0001f1f7\U0001f1fa Русский" in all_buttons
    assert "\U0001f1fa\U0001f1ff O'zbek" in all_buttons

def test_welcome_back_keyboard_has_review_and_lang_buttons():
    from keyboards import welcome_back_keyboard
    kb_uz = welcome_back_keyboard("uz")
    all_texts_uz = [btn.text for row in kb_uz.keyboard for btn in row]
    assert "Sharh qoldirish" in all_texts_uz
    assert "\U0001f310 Русский" in all_texts_uz

    kb_ru = welcome_back_keyboard("ru")
    all_texts_ru = [btn.text for row in kb_ru.keyboard for btn in row]
    assert "Оставить отзыв" in all_texts_ru
    assert "\U0001f310 O'zbek" in all_texts_ru

def test_department_keyboard_has_seven_buttons():
    from keyboards import department_keyboard
    kb = department_keyboard("uz")
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(all_buttons) == 7

def test_department_callback_data_format():
    from keyboards import department_keyboard
    kb = department_keyboard("uz")
    for row in kb.inline_keyboard:
        for btn in row:
            assert btn.callback_data.startswith("dept:")

def test_rating_keyboard_has_five_buttons():
    from keyboards import rating_keyboard
    kb = rating_keyboard()
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(all_buttons) == 5

def test_rating_callback_data_format():
    from keyboards import rating_keyboard
    kb = rating_keyboard()
    for row in kb.inline_keyboard:
        for btn in row:
            assert btn.callback_data.startswith("rating:")
            rating_val = int(btn.callback_data.split(":")[1])
            assert 1 <= rating_val <= 5
