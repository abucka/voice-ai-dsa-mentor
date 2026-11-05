import fitz
from openai import OpenAI
from dotenv import load_dotenv
import os


load_dotenv()

# Initialize the client (ensure your OPENAI_API_KEY environment variable is set)
client = OpenAI()

def call_llm():
    prompt = f"""
Prepare a list of 100 medium and easy interview data structures and algorithms questions.
For each exercise prepare a list of 3 tests to verify the solution and a template code with function 'solve' to start implemetation. 
And also how should the 'solve' function be executed.
Return JSON:
[
 {{
  "title": "title"
  "exercise": "text",
  "difficulty": "Easy|Medium"
  "tests": [
        ("abcabcbb\n", "abc\n"),
        ("bbbbb\n", "b\n"),
        ("\n", "\n")
    ]
  "template": "def solve(s):",
        "    # Return string without duplicates.",
        "    return s"
  "execution": "result = solve(s)"
 }}
]
"""
    #print(prompt)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Output the generated response
    response = response.choices[0].message.content
    print(response)
    return response


print("Thinking...")
response = call_llm()
print(response)


"""pages = []
valid = False
i = 0
for page_number, page in enumerate(doc):
    text = page.get_text()
    if "Interview Questions" in text:
        valid = True
    if valid:
        if i == 20:
            break
        #print(page_number)
        response = call_llm(text)
        print(f"{response=}\n")
        i = i + 1
       # pages.append({
       #     "page": page_number + 1,
       #     "text": text
       # })"""



