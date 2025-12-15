# TEXT NORMALIZE
user_message = Input_Handle(user_message)

# 1. DOMAIN GUARD
if not is_in_domain(user_message):
    return "Tôi chỉ hỗ trợ thông tin về địa điểm / du lịch trong hệ thống."

intent = detect_intent(user_message)
entities = extract_entities(user_message)

PROMPT = ""
citations = []# REFERENCE

memory = context_manager.get_memory()
state  = context_manager.get_state()


if intent == "suggest":
    # 3. RETRIEVAL
    places, scores = suggest_place(user_message, top_k=5)

    # 5. FORMAT CONTEXT
    raw_info, citations = format_places_info(places)

    PROMPT = format_prompt(
        SYSTEM_PROMPT_STRICT,
        user_message,
        raw_info
    )

elif intent == "info":
    context = fetch_context_by_entities(entities)

    if context is None:
        return "Tôi không có đủ thông tin để trả lời câu hỏi này."

    PROMPT = format_prompt(
        SYSTEM_PROMPT_STRICT,
        memory
        state
        user_message,
        context
    )

else:  # chat
    PROMPT = format_chat_prompt(
        SYSTEM_PROMPT_SAFE,
        user_message
    )

# 6. GENERATION
response_stream = gemini_stream(PROMPT)

full_bot_reply, confidence = collect_response(response_stream)

# 7. POST CHECK
if confidence < 0.5:
    return "Tôi không chắc chắn về câu trả lời này."

# 8. ADD CITATION
final_reply = attach_citation(full_bot_reply, citations)

# 9. SAVE HISTORY
if user_is_authenticated:
    save_conversation_history(user_id, user_message, final_reply)

return final_reply



