        # Prompt without API data
        prompt_without_api = WEATHER_RESPONSE_PROMPT.format(
            context=context,
            prompt=user_input + "\n[API OpenWeatherMap tidak digunakan. Berikan respons umum berdasarkan pengetahuan yang dimiliki.]",
            weather_info=""
        ) if is_weather else GENERAL_CONVERSATION_PROMPT.format(
            context=context,
            prompt=user_input
        )

        # Create containers for streaming responses
        tab_containers = UI.create_response_containers()

        # Initialize response dictionaries
        responses_with_api = {model: "" for model in MODELS.keys()}
        responses_without_api = {model: "" for model in MODELS.keys()}

        # Process responses sequentially - first with API
        with st.spinner("Mendapatkan respons dengan data API..."):
            for model_type in MODELS.keys():
                stream = await model_manager.get_single_model_stream(
                    model_type,
                    prompt_with_api,
                    weather_data
                )
                async for chunk in stream:
                    if chunk:
                        responses_with_api[model_type] += chunk
                        tab_containers[f"{model_type}_api"].markdown(responses_with_api[model_type])
                        await asyncio.sleep(0)

        # Then process responses without API
        with st.spinner("Mendapatkan respons tanpa data API..."):
            for model_type in MODELS.keys():
                stream = await model_manager.get_single_model_stream(
                    model_type,
                    prompt_without_api,
                    None
                )
                async for chunk in stream:
                    if chunk:
                        responses_without_api[model_type] += chunk
                        tab_containers[f"{model_type}_no_api"].markdown(responses_without_api[model_type])
                        await asyncio.sleep(0)

        # Store in chat history
        chat_entry = {
            "user_input": user_input,
            "responses_with_api": responses_with_api.copy(),
            "responses_without_api": responses_without_api.copy()
        }
        if weather_data:
            chat_entry["weather_data"] = weather_service.format_weather_data(weather_data, user_input)
        st.session_state.chat_history.append(chat_entry)

        # Add assistant response to message history (using API response as default)
        st.session_state.message_history.append({
            "role": "assistant",
            "content": responses_with_api["mistral"]
        })

if __name__ == "__main__":
    asyncio.run(main())