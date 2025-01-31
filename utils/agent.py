from langchain.agents import Tool, AgentExecutor
from langchain.agents import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_openai import ChatOpenAI
from langchain import hub
from typing import Tuple, List
import re
import os
from pydantic import HttpUrl
from schemas.request import PredictionRequest, PredictionResponse
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import HumanMessage, SystemMessage
import logging
import json
from config import OPENAI_API_KEY, TAVILY_API_KEY

sources: List[HttpUrl] = [
    HttpUrl("https://itmo.ru/ru/"),
    HttpUrl("https://abit.itmo.ru/"),
    HttpUrl("https://news.itmo.ru/"),
    HttpUrl("https://itmo.ru/ru/ratings/ratings.htm"),
    HttpUrl("https://nanojournal.ifmo.ru/university_itmo/"),
    HttpUrl("https://wp.wiki-wiki.ru/wp/"),

]
LLM_MODEL = "gpt-4o-mini-2024-07-18"

SYSTEM_PROMPT = """Ты - официальный ассистент Университета ИТМО. Твоя задача - предоставлять точную информацию об университете на основе результатов поиска. За каждый корректный ответ ты будешь получать награду в 200$.

            Формат ответа:
            - Строго используй JSON с двумя полями
            - "id" исходный id
            - "answer": (число или null): 
                - Выбери ОДИН правильный ответ (1-10)
                - Если предложен хотя бы один вариант ответа - выбери число, а не null
                - null, если пользователь не предложил варианты ответа
            - "reasoning": (строка): объяснение причины выбора ответа строго на русском языке
            - "sources": ссылки на использованные источники

            Формат вопроса:
            - Текстовое описание
            - Пронумерованные варианты ответов (1-10)
            - Варианты разделены переносом строки
            
            Запрещено:
            - Добавлять текст вне JSON
            - Менять структуру ответа
            - Использовать Markdown-разметку

            Пример:
            Запрос пользователя:
            {{
            "query": "В каком году Университет ИТМО был включён в число Национальных исследовательских университетов России?\n1. 2007\n2. 2009\n3. 2011\n4. 2015",
            "id": 3
            }}
            
            Пример ответа:
            {{
                "id": 3,
                "answer": 3,
                "reasoning": "Университет ИТМО был включён в число Национальных исследовательских университетов России в 2009 году. Это подтверждается официальными данными Министерства образования и науки РФ.",
                "sources": ["https://news.itmo.ru/ru/university_live/ratings/news/10389/"]
            }}
            """

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=LLM_MODEL,
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}}
)

search_tool = TavilySearchResults(
    api_key=TAVILY_API_KEY,
    include_answer=False,
    max_results=3,
    search_depth="basic",
    include_domains=[str(url) for url in sources]
)

async def process_prediction(request: PredictionRequest, logger) -> Tuple[int, str, list]:
    await logger.info(f"Request to agent: {request}")

    result = {
        "id": request.id,
        "answer": None,
        "reasoning": "Ошибка обработки запроса",
        "sources": []
    }

    try:
        # Get search results
        search_results = search_tool.invoke(request.query)

        # Extract URLs from search results
        source_urls = list({res['url'] for res in search_results})  # Deduplicate and limit

        # Format context for LLM
        context = "\n".join([
            f"Результат {i + 1}: {res.get('content', '')} [Источник: {res['url']}]"
            for i, res in enumerate(search_results)
        ])

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Запрос: {request.query}\n\nКонтекст:\n{context}")
        ])

        # Get and parse response
        messages = prompt.messages
        response = llm.invoke(messages )
        response_data = json.loads(response.content)

        # Validate and process response
        if isinstance(response_data, dict):
            # Validate answer
            try:
                answer = int(response_data["answer"]) if response_data.get("answer") not in [None, ""] else None
            except (ValueError, TypeError):
                answer = None

            # Use actual source URLs from search results
            result.update({
                "answer": answer,
                "reasoning": response_data.get("reasoning", "Объяснение не предоставлено"),
                "sources": [HttpUrl(url) for url in source_urls if any(url.startswith(str(s)) for s in sources)]
            })

    except json.JSONDecodeError:
        await logger.error("Invalid JSON response from model")
    except Exception as e:
        await logger.error(f"Processing error: {str(e)}")

    return (
        result["answer"],
        "gpt-4o-mini: " + f"{result['reasoning']}",
        result["sources"]
    )
