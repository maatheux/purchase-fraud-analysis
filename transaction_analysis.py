import json

import dotenv
from openai import OpenAI


def load_file(file_name):
    try:
        with open(file_name, "r") as file:
            file_data = file.read()
            return file_data
    except IOError as e:
        print(f"Error - File loading process was not finished: {e}")


def save_file(file_name, content):
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(content)
    except IOError as e:
        print(f"Error - File saving process was not finished: {e}")


def generate_response(message_list, temperature=1, response_format_json = False):
    api_key = dotenv.get_key(".env", "API_KEY")
    client = OpenAI(api_key=api_key)
    model = "gpt-4-turbo-preview"

    response_format = "json_object" if response_format_json else "text"

    response = client.chat.completions.create(
        messages=message_list,
        model=model,
        temperature=temperature,
        response_format={"type": response_format}
    )

    return response


def message_constructor(transaction_list):
    system_prompt = """
        Analise as transações financeiras a seguir e identifique se cada uma delas é uma "Possível Fraude" ou deve ser "Aprovada". 
        Adicione um atributo "Status" com um dos valores: "Possível Fraude" ou "Aprovado".
    
        Cada nova transação deve ser inserida dentro da lista do JSON.
    
        # Possíveis indicações de fraude
        - Transações com valores muito discrepantes
        - Transações que ocorrem em locais muito distantes um do outro
        
            Adote o formato de resposta abaixo para compor sua resposta.
            
        # Formato Saída 
        {
            "transacoes": [
                {
                "id": "id",
                "tipo": "crédito ou débito",
                "estabelecimento": "nome do estabelecimento",
                "horário": "horário da transação",
                "valor": "R$XX,XX",
                "nome_produto": "nome do produto",
                "localização": "cidade - estado (País)"
                "status": ""
                },
            ]
        }
        
        # Atenção
        Não adicione antes do objeto o "```json" e depois do objeto "```"
    """

    user_prompt = f"""
        Considere o CSV abaixo, onde cada linha é uma transação diferente: {transaction_list}. 
        Sua resposta deve adotar o #Formato de Resposta (apenas um json sem outros comentários)
    """

    message_list = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    return message_list


def generate_technical_opinion(transaction):
    print("2. Gerando parecer para transacao ", transaction["id"])
    system_prompt = f"""
        Para a seguinte transação, forneça um parecer, apenas se o status dela for de "Possível Fraude". Indique no parecer uma justificativa para que você identifique uma fraude.
        Transação: {transaction}

        ## Formato de Resposta
        "id": "id",
        "tipo": "crédito ou débito",
        "estabelecimento": "nome do estabelecimento",
        "horario": "horário da transação",
        "valor": "R$XX,XX",
        "nome_produto": "nome do produto",
        "localizacao": "cidade - estado (País)"
        "status": "",
        "parecer" : "Colocar Não Aplicável se o status for Aprovado"
        """

    message_list = [
        {
            "role": "user",
            "content": system_prompt
        }
    ]

    response = generate_response(message_list)

    return response.choices[0].message.content


def generate_suggestion(opinion):
    print("3. Gerando recomendações")

    system_prompt = f"""
        Para a seguinte transação, forneça uma recomendação apropriada baseada no status e nos detalhes da transação da Transação: {opinion}

        As recomendações podem ser "Notificar Cliente", "Acionar setor Anti-Fraude" ou "Realizar Verificação Manual".
        Elas devem ser escritas no formato técnico.

        Inclua também uma classificação do tipo de fraude, se aplicável. 
        """

    message_list = [
        {
            "role": "user",
            "content": system_prompt
        }
    ]

    response = generate_response(message_list)

    return response.choices[0].message.content


def main():
    data_file = load_file("./data/transacoes.csv")

    print("1.Processando análise de transação")
    message_list = message_constructor(data_file)
    response = generate_response(message_list, 0)

    response_content = response.choices[0].message.content
    print("\Conteúdo: ", response_content)
    json_result = json.loads(response_content)

    for transaction in json_result["transacoes"]:
        if transaction["status"] == "Possível Fraude":
            technical_opinion_response = generate_technical_opinion(transaction)
            suggestion = generate_suggestion(technical_opinion_response)

            save_file(f"transacao-{transaction['id']}-{transaction['nome_produto']}-{transaction['status']}.txt",
                      suggestion)


if __name__ == "__main__":
    main()
