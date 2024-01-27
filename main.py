import os
import re
import time
from openai import OpenAI


with open('config.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

keys = [
    'API_KEY', 'PROXY', 
    'SYSTEM_PROMPT_FIRST', 'SYSTEM_PROMPT_SECOND', 'USER_PROMPT_FIRST', 'USER_PROMPT_CONCLUSION', 'USER_PROMPT_BEFORE_END', 'USER_PROMPT_END', 'USER_PROMPT_TASK', 
    'MODEL', 'TEMPERATURE', 'MAX_TOKENS', 'TOP_P', 'FREQUENCY_PENALTY', 'PRESENCE_PENALTY',
    'AHREF_1', 'AHREF_2'
]

values = {key: line.split('==')[1].strip() for line in lines for key in keys if line.startswith(key)}

API_KEY = values['API_KEY']
PROXY = values['PROXY']
SYSTEM_PROMPT_FIRST = values['SYSTEM_PROMPT_FIRST']
SYSTEM_PROMPT_SECOND = values['SYSTEM_PROMPT_SECOND']
USER_PROMPT_FIRST = values['USER_PROMPT_FIRST']
USER_PROMPT_CONCLUSION = values['USER_PROMPT_CONCLUSION']
USER_PROMPT_BEFORE_END = values['USER_PROMPT_BEFORE_END']
USER_PROMPT_END = values['USER_PROMPT_END']
USER_PROMPT_TASK = values['USER_PROMPT_TASK']
MODEL = values['MODEL']
TEMPERATURE = float(values['TEMPERATURE'])
MAX_TOKENS = int(values['MAX_TOKENS'])
TOP_P = int(values['TOP_P'])
FREQUENCY_PENALTY = int(values['FREQUENCY_PENALTY'])
PRESENCE_PENALTY = int(values['PRESENCE_PENALTY'])
AHREF_1 = values['AHREF_1']
AHREF_2 = values['AHREF_2']

os.environ['http_proxy'] = PROXY
os.environ['https_proxy'] = PROXY

client = OpenAI(api_key=API_KEY)

extracted_strings = []

with open('requests.txt', 'r', encoding='utf-8') as file:
    for user_prompt in file:
    
        start_time = time.time()
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT_FIRST}]
        user_prompt = user_prompt.strip() + ' ' + USER_PROMPT_TASK
        if not user_prompt:
            continue

        messages.append({"role": "user", "content": user_prompt})
        
        # Вывод параметров запроса
        request_parameters = {
            "model": MODEL,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "top_p": TOP_P,
            "frequency_penalty": FREQUENCY_PENALTY,
            "presence_penalty": PRESENCE_PENALTY,
        }
        
        try:
            response = client.chat.completions.create(**request_parameters)
            assistant_message = response.choices[0].message.content

            extracted = re.findall(r'(<h(?!1)\d+>.*?<\/h\d+>)', assistant_message, re.IGNORECASE)
            extracted_strings.extend(extracted)

            messages.remove({"role": "system", "content": SYSTEM_PROMPT_FIRST})
            messages.append({"role": "system", "content": SYSTEM_PROMPT_SECOND})
            messages.remove({"role": "user", "content": user_prompt})
            messages.append({"role": "user", "content": user_prompt})
            messages.append({"role": "assistant", "content": assistant_message})

        except Exception as e:
            print(f'Произошла ошибка: {e}')
            break

        messages.append({"role": "user", "content": USER_PROMPT_FIRST})

        try:
            response = client.chat.completions.create(**request_parameters)
            assistant_message = response.choices[0].message.content

            messages.append({"role": "assistant", "content": assistant_message})
            
        except Exception as e:
            print(f'Произошла ошибка: {e}')
        
        gpt_responses_titles = []

        for extracted_string in extracted_strings:
            
            extracted_string = f'Напиши раздел {extracted_string}'
            messages.append({"role": "user", "content": extracted_string})

            try:
                # Отправляем запрос
                response = client.chat.completions.create(**request_parameters)
                assistant_message = response.choices[0].message.content

                messages.append({"role": "assistant", "content": assistant_message})
                
                # Сохраняем ответ в список
                gpt_responses_titles.append(f'{assistant_message}\n\n')
                
            except Exception as e:
                print(f'Произошла ошибка: {e}')
                break
        
        messages.append({"role": "user", "content": USER_PROMPT_CONCLUSION})

        try:
            response = client.chat.completions.create(**request_parameters)
            assistant_message = response.choices[0].message.content

            messages.append({"role": "assistant", "content": assistant_message})
            
            gpt_responses_conc = assistant_message
            
        except Exception as e:
            print(f'Произошла ошибка: {e}')

        messages.append({"role": "user", "content": USER_PROMPT_BEFORE_END})

        try:
            response = client.chat.completions.create(**request_parameters)
            assistant_message = response.choices[0].message.content

            messages.append({"role": "assistant", "content": assistant_message})
            
            gpt_responses_begin = assistant_message
            
        except Exception as e:
            print(f'Произошла ошибка: {e}')

        article = []
        article.append(gpt_responses_begin)
        article.extend(gpt_responses_titles)
        article.append(gpt_responses_conc)
        
        messages.append({"role": "user", "content": USER_PROMPT_END})

        try:
            response = client.chat.completions.create(**request_parameters)
            assistant_message = response.choices[0].message.content

            gpt_responses_markup = assistant_message
    
        except Exception as e:
            print(f'Произошла ошибка: {e}')
        

        result = gpt_responses_markup.replace("###Основной текст статьи###", "\n".join(article))
        
        result = re.sub(r'<a href="#">', lambda match: f'<a href="{AHREF_1}">', result, count=1)
        result = re.sub(r'<a href="#">', lambda match: f'<a href="{AHREF_2}">', result, count=1)
        
        messages = []
        
        start_index = result.find('[__slug__]\n')
        end_index = result.find('\n\n', start_index)

        if start_index != -1 and end_index != -1:
            file_name = result[start_index + 11: end_index]

        with open(file_name + ".txt", "w", encoding='utf-8') as file:
            file.write(result)
            
        result = None
            
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Итерация выполнена за {execution_time} секунд")