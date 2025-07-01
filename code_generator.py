import os
import requests
import re
from dotenv import load_dotenv
from groq import Groq  # Import Groq client

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
CODE_MODEL = "llama3-70b-8192"

def is_code_request(query: str) -> bool:
    """
    More precise detection of when users explicitly request code
    Only returns True when user clearly wants implementation/code snippets
    """
    query_lower = query.lower().strip()
    
    # Explicit code request phrases - these clearly indicate wanting code
    explicit_code_requests = [
        "write code", "write a function", "write a program", "write a script",
        "show me code", "give me code", "create code", "generate code",
        "implement", "code for", "code to", "function to", "script to",
        "how to code", "how to implement", "how to program",
        "code example", "coding example", "example code",
        "create a function", "create a method", "create a class",
        "build a", "develop a", "program that", "script that",
        "show implementation", "write implementation"
    ]
    
    # Programming-specific implementation requests
    implementation_requests = [
        "api endpoint", "database connection", "sql query",
        "algorithm implementation", "data structure implementation",
        "component in react", "function in python", "method in java",
        "class in", "module in", "package in"
    ]
    
    # Check for explicit code requests
    for phrase in explicit_code_requests:
        if phrase in query_lower:
            return True
    
    # Check for implementation requests
    for phrase in implementation_requests:
        if phrase in query_lower:
            return True
    
    # Check for specific language + implementation patterns
    languages = ["python", "javascript", "java", "c++", "rust", "go", "php", "ruby", "swift", "kotlin"]
    implementation_verbs = ["write", "create", "build", "implement", "develop", "code", "program"]
    
    for lang in languages:
        for verb in implementation_verbs:
            if f"{verb} in {lang}" in query_lower or f"{verb} a {lang}" in query_lower:
                return True
    
    # Exclude conceptual/educational questions that mention programming
    educational_excludes = [
        "what is", "what are", "explain", "describe", "tell me about",
        "benefits of", "advantages of", "disadvantages of", "pros and cons",
        "how does", "why does", "when to use", "difference between",
        "list of", "give me questions", "what questions", "quiz about",
        "best practices", "principles of", "concepts of"
    ]
    
    for exclude in educational_excludes:
        if exclude in query_lower:
            return False
    
    return False

def is_educational_request(query: str) -> bool:
    """
    Detect when user is asking for educational/conceptual information
    rather than implementation
    """
    query_lower = query.lower().strip()
    
    educational_indicators = [
        "explain", "what is", "what are", "describe", "tell me about",
        "how does", "why does", "benefits", "advantages", "disadvantages", 
        "difference between", "compare", "pros and cons",
        "give me questions", "list questions", "quiz", "test questions",
        "best practices", "principles", "concepts", "theory",
        "overview of", "introduction to", "basics of",
        "give me", "list", "provide", "suggest", "recommend"
    ]
    
    return any(indicator in query_lower for indicator in educational_indicators)

def structure_code_explanation(code_response, language):
    """
    Takes a code response and adds structured sections with deep reasoning if they don't already exist
    """
    # Check if the response already has section headers
    has_sections = re.search(r'#{2,3}\s+\w+', code_response)
    
    if has_sections:
        return code_response
    
    # Extract the first code block
    code_block_match = re.search(r'```(?:\w*)\n([\s\S]*?)\n```', code_response)
    
    if not code_block_match:
        return code_response
    
    # Get text before and after the code block
    full_match = code_block_match.group(0)
    text_before = code_response[:code_block_match.start()]
    text_after = code_response[code_block_match.end():]
    
    # Structure the response with deep reasoning sections
    structured_response = ""
    
    # Add problem analysis section if there's text before the code
    if text_before.strip():
        structured_response += "## Problem Analysis\n\n" + text_before.strip() + "\n\n"
    else:
        structured_response += "## Problem Analysis\n\nHere's my approach to solving this problem:\n\n"
    
    # Add solution strategy section based on the language
    if language == "move":
        structured_response += "## Solution Strategy\n\n"
        structured_response += "For this Move implementation, I'm focusing on:\n\n"
        structured_response += "- **Resource Safety**: Ensuring proper resource handling following Move's ownership model\n"
        structured_response += "- **Module Structure**: Creating clear module boundaries with appropriate access controls\n"
        structured_response += "- **Type Safety**: Leveraging Move's type system for compile-time guarantees\n\n"
    elif language == "rust":
        structured_response += "## Solution Strategy\n\n"
        structured_response += "For this Rust implementation, I'm focusing on:\n\n"
        structured_response += "- **Memory Safety**: Using Rust's ownership system to prevent memory issues\n"
        structured_response += "- **Error Handling**: Proper use of Result and Option types\n"
        structured_response += "- **Performance**: Efficient algorithms while maintaining safety\n\n"
    elif language == "python":
        structured_response += "## Solution Strategy\n\n"
        structured_response += "For this Python implementation, I'm focusing on:\n\n"
        structured_response += "- **Readability**: Following Python's philosophy of clear, readable code\n"
        structured_response += "- **Flexibility**: Creating a solution that's easy to modify and extend\n"
        structured_response += "- **Best Practices**: Following modern Python conventions\n\n"
    else:
        structured_response += "## Solution Strategy\n\n"
        structured_response += "My implementation focuses on:\n\n"
        structured_response += "- **Readability**: Writing clear, self-documenting code\n"
        structured_response += "- **Maintainability**: Structuring code for easy updates and extensions\n"
        structured_response += "- **Efficiency**: Balancing performance with code clarity\n\n"
    
    # Add implementation section with code block
    structured_response += "## Implementation\n\n"
    structured_response += full_match + "\n\n"
    
    # Add code walkthrough section if there's text after the code
    if text_after.strip():
        structured_response += "## Code Walkthrough\n\n" + text_after.strip() + "\n\n"
    else:
        structured_response += "## Code Walkthrough\n\n"
        structured_response += "Let's examine how this code works:\n\n"
        structured_response += "1. First, we set up the necessary structure and imports\n"
        structured_response += "2. Then we implement the core functionality\n"
        structured_response += "3. Finally, we handle edge cases and optimizations\n\n"
    
    # Add usage example section
    structured_response += "## Usage Example\n\n"
    structured_response += f"Here's how you would use this code:\n\n"
    structured_response += f"```{language}\n# Example usage would typically be shown here\n```\n\n"
    
    # Add testing considerations section
    structured_response += "## Testing Considerations\n\n"
    if language == "move":
        structured_response += "When testing this Move code, consider:\n\n"
        structured_response += "- Unit testing with `#[test]` functions to verify functionality\n"
        structured_response += "- Testing resource creation, transfer, and destruction scenarios\n"
        structured_response += "- Verifying proper permission handling and access controls\n\n"
    elif language == "rust":
        structured_response += "When testing this Rust code, consider:\n\n"
        structured_response += "- Unit tests to verify each component works correctly\n"
        structured_response += "- Testing edge cases like empty inputs or maximum values\n"
        structured_response += "- Property-based testing for more complex functionality\n\n"
    elif language == "python":
        structured_response += "When testing this Python code, consider:\n\n"
        structured_response += "- Unit tests using pytest or unittest\n"
        structured_response += "- Testing with various input types and edge cases\n"
        structured_response += "- Integration testing if this interacts with other components\n\n"
    else:
        structured_response += "When testing this code, consider:\n\n"
        structured_response += "- Writing unit tests to verify core functionality\n"
        structured_response += "- Testing edge cases and boundary conditions\n"
        structured_response += "- Verifying error handling works as expected\n\n"
    
    # Add requirements and potential optimizations
    structured_response += "## Requirements\n\n"
    if language == "python":
        structured_response += "This code requires Python 3.6+ and has no external dependencies beyond the standard library.\n\n"
    elif language == "javascript":
        structured_response += "This code can run in any modern browser or Node.js environment.\n\n"
    elif language == "move":
        structured_response += "This code is written in Move language and requires the Move compiler. It's compatible with Sui Move or Aptos Move environments.\n\n"
    elif language == "rust":
        structured_response += "This code requires Rust 1.40+ and uses only standard library features.\n\n"
    
    structured_response += "## Potential Optimizations\n\n"
    structured_response += "If needed, this implementation could be further optimized by:\n\n"
    structured_response += "- Improving algorithm efficiency for large inputs\n"
    structured_response += "- Reducing memory usage with more efficient data structures\n"
    structured_response += "- Adding caching for frequently accessed values\n\n"
    
    return structured_response

def needs_deep_technical_reasoning(query):
    """
    Determine if a code-related query would benefit from deeper technical reasoning
    """
    # Keywords that suggest complex technical implementation
    complex_keywords = [
        "architecture", "design pattern", "system", "algorithm", "optimize", 
        "efficient", "performance", "scalable", "secure", "robust", 
        "trade-off", "comparison", "approach", "best practice", "framework", 
        "complex", "advanced", "production-ready", "enterprise", "modular",
        "maintainable", "flexible", "extensible", "customizable", "elegant"
    ]
    
    query_lower = query.lower()
    
    # Check for complexity keywords
    complexity_score = sum(1 for keyword in complex_keywords if keyword in query_lower)
    
    # Check for indicators of wanting detailed explanation
    wants_explanation = any(exp in query_lower for exp in [
        "explain", "understand", "clarify", "detail", "thoroughly", "comprehensive",
        "in-depth", "elaborate", "breakdown", "step by step", "walkthrough"
    ])
    
    # Check for specific technical challenges
    technical_challenges = any(challenge in query_lower for challenge in [
        "concurrency", "parallelism", "asynchronous", "distributed", 
        "memory management", "garbage collection", "optimization", 
        "caching", "scaling", "security", "authentication", "authorization",
        "encryption", "validation", "error handling", "fault tolerance",
        "recovery", "persistence", "storage", "indexing", "query optimization"
    ])
    
    # Total score based on factors
    total_score = complexity_score + (2 if wants_explanation else 0) + (2 if technical_challenges else 0)
    
    return total_score >= 3  # Threshold for deep technical reasoning

def generate_code(query: str) -> str:
    """
    Generate code using a language model based on the user query
    """
    # Check if this is a follow-up query using conversation context
    is_follow_up = any(kw in query.lower() for kw in [
        "previous", "context", "conversation", "earlier", "before", 
        "you said", "as discussed", "fix", "modify", "update", "improve",
        "continuing", "following up"
    ])
    
    # Detect language from the query or use context
    language = detect_language(query)
    
    # Determine if query needs deep technical reasoning
    needs_deep_reasoning = needs_deep_technical_reasoning(query)
    reasoning_level = "deep" if needs_deep_reasoning else "standard"
    print(f"Using {reasoning_level} technical reasoning for code generation")
    
    # Common instructions for all code responses with deep reasoning
    response_structure = ""
    
    if needs_deep_reasoning:
        response_structure = """
DEEP TECHNICAL REASONING APPROACH:
Before presenting code, I will think through the problem systematically and thoroughly:
1. First, I'll analyze what the user is asking for and identify all requirements and constraints
2. Explore multiple implementation approaches and evaluate their tradeoffs in detail
3. Consider time complexity, space complexity, and other performance characteristics
4. Think about edge cases, error handling, and robustness
5. Explain design patterns or architectural principles that inform my solution
6. Consider maintainability, extensibility, and how the code might evolve
7. Justify technical decisions with clear reasoning

DETAILED RESPONSE STRUCTURE:
1. Start with a comprehensive analysis of the problem and requirements
2. Explain my reasoning process and technical decision-making in detail
3. Compare alternative approaches with pros and cons of each
4. Present the complete code solution with extensive comments
5. Provide a thorough walkthrough of the implementation explaining every significant part
6. Include a detailed discussion of trade-offs, optimizations, and potential improvements
7. Address edge cases, error handling, and potential limitations explicitly
8. Include testing strategies and considerations for production use

FORMAT GUIDELINES:
- Use ## for main sections and ### for subsections
- Structure solutions with detailed sections:
  * ## Problem Analysis
  * ## Design Considerations
  * ## Implementation Approaches
  * ## Technical Decisions and Tradeoffs
  * ## Implementation
  * ## Detailed Code Walkthrough
  * ## Edge Cases and Error Handling
  * ## Testing and Validation
  * ## Performance Considerations
  * ## Potential Optimizations
- Use bullet points for detailed lists of considerations
- Bold key technical concepts using **bold text**
- Include algorithm complexity analysis (time/space) where relevant
"""
    else:
        response_structure = """
REASONING APPROACH:
Before presenting code, I will think through the problem clearly:
1. First, I'll analyze what the user is asking for and identify the requirements
2. Consider appropriate implementation approaches and their tradeoffs
3. Select the most suitable solution based on clarity and effectiveness
4. Break down complex problems into manageable components
5. Consider important edge cases and how to handle them

RESPONSE STRUCTURE:
1. Start with a brief overview of what the code accomplishes
2. Explain my implementation approach and key decisions
3. Present the complete code solution in a well-formatted code block
4. After the code, provide a section-by-section explanation of how it works
5. Include information about any libraries or dependencies required
6. Address potential edge cases and limitations

FORMAT GUIDELINES:
- Use ## or ### for section headings (e.g., ### Code Explanation)
- Use bullet points for listing features or steps
- Bold important concepts using **bold text**
- For multi-part code explanations, use numbered lists
"""
    
    # Create language-specific system prompts for better code generation
    language_specific_instructions = {
        "move": f"""You are an expert Move language programmer. When writing Move code:
- Always use correct Move syntax, including proper module, struct, and function definitions
- Follow best practices for Move development including proper use of resources
- Include necessary imports with the 'use' statement
- Properly handle ownership and borrowing patterns
- Add helpful comments to explain complex operations
- For Sui Move, use the correct module structure with appropriate capabilities (store, key, drop)
- For Aptos Move, follow the Aptos-specific conventions
- Structure modules with public/entry functions as appropriate
- Include test functions where beneficial marked with #[test]

{response_structure}""",
        
        "rust": f"""You are an expert Rust programmer. When writing Rust code:
- Use proper ownership and borrowing patterns
- Handle errors appropriately with Result and Option types
- Use proper struct and trait implementations
- Follow Rust naming conventions and idiomatic Rust practices

{response_structure}""",
        
        "solidity": f"""You are an expert Solidity developer. When writing Solidity code:
- Follow best practices for security, including reentrancy protection
- Use proper version pragmas
- Handle errors and exceptions appropriately
- Use appropriate visibility modifiers
- Consider gas optimization where relevant

{response_structure}""",
        
        "python": f"""You are an expert Python programmer. When writing Python code:
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write clean, readable, and efficient code
- Include docstrings and comments as needed

{response_structure}""",
        
        "typescript": f"""You are an expert TypeScript programmer. When writing TypeScript code:
- Use proper type definitions and interfaces
- Follow TypeScript best practices
- Write clean, readable code with proper error handling

{response_structure}""",
    }
    
    # Default system prompt for languages without specific instructions
    default_system_prompt = f"""You are an expert programmer. Generate clean, efficient, and well-commented code that follows best practices for the requested language.

{response_structure}"""
    
    # Get language-specific instructions or use default
    system_prompt = language_specific_instructions.get(language, default_system_prompt)
    
    # Add context awareness to system prompt if this appears to be a follow-up request
    if is_follow_up:
        system_prompt += """
When modifying existing code or answering follow-up questions:
- Pay close attention to the conversation history and previous code
- Make sure your changes are consistent with the context
- Clearly explain what was changed and why
- If relevant code was provided earlier, use that as a reference point"""
    
    # Create the user message with the query and language
    user_message = f"Generate {language} code for: {query}"
    
    # Initialize the Groq client
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    try:
        # Generate response using the language model
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # Using Llama 3 70B model for high-quality code generation
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,  # Lower temperature for more precise code generation
            max_tokens=4000
        )
        
        code_response = response.choices[0].message.content
        
        # Process the response to ensure code is properly formatted with language tag
        # If the response already has markdown code blocks, ensure they have the correct language
        if "```" in code_response:
            # Replace language tags or add them if missing
            code_response = re.sub(r'```(?:\w*)', f'```{language}', code_response, count=1)
            # Make sure closing backticks are present
            if code_response.count('```') == 1:
                code_response += '\n```'
        else:
            # Wrap the entire response in a code block with language tag
            code_response = f'```{language}\n{code_response}\n```'
        
        # Structure the code response for better readability
        structured_response = structure_code_explanation(code_response, language)
        
        return structured_response
    except Exception as e:
        return f"Error generating code: {str(e)}"

def detect_language_from_code(code_text):
    """Detect the programming language from code for better UI display"""
    # Common language patterns
    patterns = {
        "python": [r"def\s+\w+\s*\(", r"import\s+\w+", r"from\s+\w+\s+import", r"class\s+\w+:"],
        "javascript": [r"function\s+\w+\s*\(", r"const\s+\w+\s*=", r"let\s+\w+\s*=", r"var\s+\w+\s*=", r"=>"],
        "typescript": [r":\s*\w+(\[\])?\s*=", r"interface\s+\w+", r"type\s+\w+\s*="],
        "java": [r"public\s+class", r"private\s+\w+\s+\w+", r"protected\s+\w+", r"void\s+\w+\s*\("],
        "c++": [r"#include", r"std::", r"template<", r"namespace\s+\w+"],
        "c#": [r"namespace\s+\w+", r"using\s+\w+;", r"public\s+class", r"private\s+\w+\s+\w+;"],
        "rust": [r"fn\s+\w+", r"let\s+mut", r"struct\s+\w+", r"impl\s+\w+", r"pub\s+fn"],
        "go": [r"func\s+\w+", r"package\s+\w+", r"import\s+\(", r"type\s+\w+\s+struct"],
        "ruby": [r"def\s+\w+\s*\n", r"class\s+\w+\s*<", r"require", r"end"],
        "php": [r"\$\w+\s*=", r"<?php", r"namespace\s+\w+;", r"function\s+\w+\s*\("],
        "swift": [r"func\s+\w+\s*\(", r"var\s+\w+\s*:", r"let\s+\w+\s*:", r"class\s+\w+"],
        "kotlin": [r"fun\s+\w+", r"val\s+\w+", r"var\s+\w+", r"class\s+\w+"],
        "sql": [r"SELECT\s+.*\s+FROM", r"INSERT\s+INTO", r"UPDATE\s+\w+\s+SET", r"CREATE\s+TABLE"],
        "html": [r"<html", r"<div", r"<body", r"<head", r"<script"],
        "css": [r"\.\w+\s*{", r"#\w+\s*{", r"@media", r"margin:", r"padding:"],
        "move": [r"module\s+\w+", r"resource\s+\w+", r"public\s+fun", r"struct\s+\w+", r"has\s+key", 
                r"has\s+drop", r"has\s+store", r"has\s+copy", r"use\s+0x\w+::\w+", r"acquires\s+\w+", 
                r"address\s+0x\w+", r"friend\s+\w+::\w+", r"fun\s+\w+", r"native\s+fun", r"const\s+\w+:"], 
        "solidity": [r"contract\s+\w+", r"function\s+\w+\s*\(.*\)\s*(public|private|external|internal)", r"pragma\s+solidity"]
    }
    
    for language, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, code_text, re.IGNORECASE):
                return language
    
    return "code"  # Default if no language is detected

def detect_language(query: str) -> str:
    """
    Detect programming language from the query with enhanced support for Move language
    """
    # Enhanced language mapping with more specific keywords and patterns
    language_patterns = {
        # Move language - enhanced detection with more keywords and patterns
        'move': [
            r'\bmove\b', r'\bmodule\s+\w+\s*{', r'\bstruct\s+\w+\s*{', r'\bscript\s*{', 
            r'\bresource\b', r'\bacquires\b', r'\bpublic\s+fun\b', r'\bfun\b', r'\bsui\b', 
            r'\baptos\b', r'\bdiem\b', r'\blibra\b', r'\bstd::move_to\b', r'\bmove_to\b',
            r'\bvector<\w+>\b', r'\bsigner\b', r'\bcoin\b', r'\bmove\s+language\b',
            r'#\[test\]', r'\bpublic\s+entry\b', r'\bentry\s+fun\b', r'\bhasPublishingCapability\b',
            r'\btransaction\s*{', r'\buse\s+\w+::\w+\s*;', r'\b0x\w+::',
            r'\.move$', r'\.mvir$', r'\bstorage\b', r'\bkey\b && \bstore\b'
        ],
        'python': [
            r'\.py$', r'\bpython\b', r'\bdef\s+\w+\s*\(', r'\bimport\s+\w+\b', r'\bfrom\s+\w+\s+import\b',
            r'\bclass\s+\w+\s*:', r'\bif\s+__name__\s*==\s*["\']__main__["\']\s*:',
            r'\bprint\w*\s*\('
        ],
        'javascript': [
            r'\.js$', r'\bjavascript\b', r'\blet\b', r'\bconst\b', r'\bfunction\b', r'\b=>\b',
            r'\bdocument\.\w+\b', r'\bwindow\.\w+\b', r'\bconsole\.log\b'
        ],
        'typescript': [
            r'\.ts$', r'\btypescript\b', r'\binterface\b', r'\btype\b', r'\bnamespace\b',
            r'\b:\s*\w+\b', r'\bas\s+\w+\b'
        ],
        'java': [
            r'\.java$', r'\bjava\b', r'\bclass\s+\w+\s*\{', r'\bpublic\s+static\s+void\s+main\b',
            r'\bSystem\.out\.print\w*\b'
        ],
        'c++': [
            r'\.cpp$', r'\bc\+\+\b', r'\bcpp\b', r'\b#include\s*<\w+>\b', r'\bstd::\w+\b',
            r'\bvoid\s+\w+\s*\(', r'\bnamespace\s+\w+\s*\{'
        ],
        'c#': [
            r'\.cs$', r'\bc#\b', r'\bcsharp\b', r'\busing\s+\w+;', r'\bnamespace\s+\w+\s*\{',
            r'\bpublic\s+class\s+\w+\s*\{', r'\bConsole\.Write\w*\b'
        ],
        'go': [
            r'\.go$', r'\bgolang\b', r'\bgo\b', r'\bfunc\s+\w+\s*\(', r'\bpackage\s+\w+\b',
            r'\bimport\s+\(', r'\bfmt\.\w+\b'
        ],
        'rust': [
            r'\.rs$', r'\brust\b', r'\bfn\s+\w+\s*\(', r'\blet\s+mut\b', r'\bstruct\s+\w+\s*\{',
            r'\benum\s+\w+\s*\{', r'\bimpl\s+\w+\s*(\s*for\s*\w+\s*)?\{', r'\bmatch\b', 
            r'\bcargo\b', r'\buse\s+\w+::'
        ],
        'solidity': [
            r'\.sol$', r'\bsolidity\b', r'\bcontract\s+\w+\s*\{', r'\bfunction\s+\w+\s*\(',
            r'\bmapping\s*\(', r'\baddress\b', r'\buint\d*\b', r'\bevent\b', r'\bpragma\s+solidity\b'
        ],
        'html': [
            r'\.html$', r'\bhtml\b', r'\b<html\b', r'\b<div\b', r'\b<p\b', r'\b<body\b',
            r'\b</\w+>\b'
        ],
        'css': [
            r'\.css$', r'\bcss\b', r'\b\w+\s*{\s*\w+', r'\b\.\w+\s*{', r'\b#\w+\s*{',
            r'\bmargin\b', r'\bpadding\b', r'\bcolor\b', r'\bfont-size\b'
        ],
        'sql': [
            r'\.sql$', r'\bsql\b', r'\bselect\b', r'\bfrom\b', r'\bwhere\b', r'\bjoin\b',
            r'\binsert\s+into\b', r'\bcreate\s+table\b', r'\bdelete\s+from\b'
        ],
    }

    # Check for explicit language mentions first
    query_lower = query.lower()
    
    # Direct language mentions take precedence
    if re.search(r'(?:in|using|with)\s+move\s+(?:language|code)', query_lower) or re.search(r'(?:write|generate)\s+move\s+(?:code|script)', query_lower):
        return 'move'
        
    # Check for other explicit language mentions
    for lang, patterns in language_patterns.items():
        for explicit_pattern in [rf'(?:in|using|with)\s+{lang}\s+(?:language|code)', rf'(?:write|generate)\s+{lang}\s+(?:code|script)']:
            if re.search(explicit_pattern, query_lower):
                return lang
    
    # Now check for language-specific patterns and count matches
    lang_scores = {}
    for lang, patterns in language_patterns.items():
        lang_scores[lang] = 0
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # Give higher weight to Move language patterns to improve its detection
                if lang == 'move':
                    lang_scores[lang] += 1.5
                else:
                    lang_scores[lang] += 1
    
    # If we have a strong signal for a language
    if lang_scores:
        # Get the language with the highest score
        detected_lang = max(lang_scores.items(), key=lambda x: x[1])
        if detected_lang[1] > 0:
            return detected_lang[0]
    
    # Default to a general plain text if no language is detected
    return "plaintext"

# Example usage:
if __name__ == "__main__":
    user_query = input("Ask for code: ")
    if is_code_request(user_query):
        print(generate_code(user_query))
    else:
        print("Not a code request.")
