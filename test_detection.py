import code_generator

# Test educational requests
test_queries = [
    'explain how bubble sort works',
    'give me 10 questions about networking',
    'what are the benefits of Python',
    'write a bubble sort function in Python',
    'implement a login system',
    'how to code a web scraper'
]

print("Testing improved code detection logic:")
print("=" * 50)

for query in test_queries:
    is_code = code_generator.is_code_request(query)
    is_educational = code_generator.is_educational_request(query)
    print(f'Query: {query}')
    print(f'  Code Request: {is_code}')
    print(f'  Educational: {is_educational}')
    print()
