from setuptools import setup, find_packages

setup(
    name='telegram_openai_assistant',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.8",  
        "openai>=1.16.0",
        "python-dotenv>=1.0.0",
    ]
,
    entry_points={
        'console_scripts': [
            'chatbot = telegram_openai_assistant.bot:main',
        ],
    },
)
