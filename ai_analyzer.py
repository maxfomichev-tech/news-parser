
import aiohttp
from config import config

class AIAnalyzer:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"

    async def analyze_news(self, news_text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        prompt = f"""Ты — профессиональный аналитик новостей. Проанализируй новости и создай структурированный отчет.

📊 Основные темы (3-5 тем с кратким описанием)
🔥 Главные события (2-3 события с контекстом)
📈 Тренды (что набирает обороты)
💡 Вывод (общая оценка ситуации)

Будь объективным и лаконичным.

Новости для анализа:
{news_text[:4000]}"""

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 1000
        }

        timeout = aiohttp.ClientTimeout(total=30)  # Groq очень быстрый

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self.url,
                headers=headers,
                json=payload
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API {response.status}: {error_text[:200]}")

                data = await response.json()
                return data['choices'][0]['message']['content'].strip()

    async def analyze_with_fallback(self, news_text: str) -> str:
        try:
            return await self.analyze_news(news_text)
        except Exception as e:
            print(f"AI Error: {e}")
            lines = [l.strip() for l in news_text.split('\n') if l.strip() and l[0].isdigit()]
            headers = [l.split('. ', 1)[1] if '. ' in l else l for l in lines[:5]]

            return (
                "⚠️ *Анализ недоступен*\n\n"
                f"_Ошибка: {str(e)[:100]}_\n\n"
                "*Последние новости:*\n" +
                '\n'.join([f"• {h[:80]}..." for h in headers])
            )
