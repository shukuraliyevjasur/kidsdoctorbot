import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_uz_key_returns_uz_string():
    from locales import _
    assert _("enter_name", "uz") == "Ismingizni kiriting:"

def test_ru_key_returns_ru_string():
    from locales import _
    assert _("enter_name", "ru") == "Введите ваше имя:"

def test_unknown_lang_falls_back_to_uz():
    from locales import _
    assert _("enter_name", "xx") == "Ismingizni kiriting:"

def test_unknown_key_returns_key_itself():
    from locales import _
    assert _("nonexistent_key", "uz") == "nonexistent_key"

def test_welcome_back_contains_placeholder():
    from locales import _
    result = _("welcome_back", "ru")
    assert "{name}" in result

def test_all_departments_present_in_both_langs():
    from locales import _
    departments = ["pediatrician", "dentist", "ent", "orthopedist", "allergist", "massage", "diagnostics"]
    for dept in departments:
        assert _("dept_" + dept, "uz") != "dept_" + dept, f"Missing UZ translation for {dept}"
        assert _("dept_" + dept, "ru") != "dept_" + dept, f"Missing RU translation for {dept}"
