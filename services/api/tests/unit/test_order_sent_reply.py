"""Once an order went through, the reply is the model's own words, but never a wrong order number."""
from pino_yard.application.ai.agent_service import confirmed_order_reply


def test_the_models_words_are_kept():
    assert confirmed_order_reply("تمام، طلبك وصل المطبخ!", "PY-104", "ar") == "تمام، طلبك وصل المطبخ!"
    assert confirmed_order_reply("وصل طلبك PY-104 للمطعم", "PY-104", "ar") == "وصل طلبك PY-104 للمطعم"


def test_a_wrong_or_missing_reply_gives_the_servers_sentence():
    assert confirmed_order_reply("طلبك PY-101 بالطريق", "PY-104", "ar").startswith("تم إرسال طلبك رقم PY-104")
    assert confirmed_order_reply("", "PY-104", "en").startswith("Your order PY-104")
