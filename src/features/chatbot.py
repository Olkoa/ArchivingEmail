from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def setup_mistral_7b():
    """Initialize the Mistral 7B model."""
    # Choose the Mistral 7B Instruct model
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Load model with quantization to reduce memory usage
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",  # Uses GPU if available
        load_in_4bit=True,  # 4-bit quantization for memory efficiency
        trust_remote_code=True
    )

    return model, tokenizer


def answer_with_mistral(question, rag_answer):
    """Generate an answer using Mistral 7B based on RAG results."""
    model, tokenizer = setup_mistral_7b()

    # Format prompt for Mistral instruction model
    prompt = f"""<s>[INST] Based on the following information, please answer the question directly and concisely.

Question: {question}

Retrieved Information:
{rag_answer} [/INST]"""

    # Generate response
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_new_tokens=200,
            temperature=0.1,  # Low temperature for more focused answers
            do_sample=True,
            top_p=0.95
        )

    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response.strip()


if __name__ == "__main__":
    # Example usage
    question = "Avez vous des informations sur le projet de numérisation ?"
    rag_answer = """D'après les emails récupérés, j'ai trouvé des informations liées à votre question.
    Voici ce que j'ai trouvé:
    * Email de thomas.berger@archives-vaucluse.fr mentionne: "Bonjour Lucie,
    Concernant le projet de numérisation du fonds Archives hospitalières, nous avons reçu le devis de la société prestataire. Le montant s'élève à 122 euros pour environ 61 documents.
    Pouvons-nous en discuter lors de notre prochaine réunion?
    Bien cordialement, Thomas Berger Responsable numérisation Archives départementales du Vaucluse Tél: 04.90.86.16.20 "

    * Email de m.lambert@education.gouv.fr mentionne: "Bonjour Marie,
    Concernant le projet de numérisation du fonds Archives judiciaires, nous avons reçu le devis de la société prestataire. Le montant s'élève à 658 euros pour environ 489 documents.
    Pouvons-nous en discuter lors de notre prochaine réunion? """

    answer = answer_with_mistral(question, rag_answer)
    print(answer)
