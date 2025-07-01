import os
import re
from dotenv import load_dotenv
from groq import Groq  # Import Groq client

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DOC_MODEL = "llama3-70b-8192"

def is_document_request(query: str) -> bool:
    """
    Detect if the user is requesting a document to be generated
    """
    document_keywords = [
        # Document types
        "cv", "resume", "curriculum vitae", "cover letter", "proposal", "business plan",
        "report", "summary", "memo", "brief", "minutes", "notes", "presentation",
        "whitepaper", "case study", "press release", "newsletter", "executive summary",
        "project plan", "marketing plan", "swot analysis", "financial report", 
        "thesis", "dissertation", "research paper", "essay", "assignment", "speech",
        "statement of purpose", "personal statement", "recommendation letter",
        
        # Action verbs
        "create document", "write document", "generate document", "draft a", "write a", 
        "create a", "make a", "compose a", "prepare a", "develop a", "produce a",
        "help me write", "help me create", "need a template for", "format for",
        
        # Format indicators
        "format", "template", "layout", "structure", "professional", "formal", 
        "official", "document", "paperwork", "documentation", "letterhead"
    ]
    return any(kw.lower() in query.lower() for kw in document_keywords)

def detect_document_type(query: str) -> str:
    """
    Detect the type of document requested
    """
    document_types = {
        "cv": ["cv", "resume", "curriculum vitae"],
        "cover_letter": ["cover letter", "job application letter", "application letter"],
        "proposal": ["proposal", "business proposal", "project proposal"],
        "business_plan": ["business plan", "startup plan", "company plan"],
        "report": ["report", "business report", "technical report", "analysis report"],
        "summary": ["summary", "executive summary", "brief summary"],
        "notes": ["notes", "meeting notes", "lecture notes", "study notes"],
        "presentation": ["presentation", "slides", "slide deck", "powerpoint"],
        "whitepaper": ["whitepaper", "white paper", "technical paper"],
        "press_release": ["press release", "media release", "news release"],
        "newsletter": ["newsletter", "company newsletter", "email newsletter"],
        "project_plan": ["project plan", "project schedule", "project timeline"],
        "marketing_plan": ["marketing plan", "marketing strategy", "go to market"],
        "research_paper": ["research paper", "academic paper", "scientific paper"],
        "essay": ["essay", "academic essay", "argumentative essay"],
        "speech": ["speech", "public speech", "presentation speech"],
        "personal_statement": ["personal statement", "statement of purpose", "application statement"],
        "recommendation": ["recommendation letter", "reference letter", "letter of recommendation"]
    }
    
    query_lower = query.lower()
    
    for doc_type, keywords in document_types.items():
        if any(keyword in query_lower for keyword in keywords):
            return doc_type
    
    # Default to generic document if no specific type is found
    return "generic_document"

def structure_document_output(document_text, document_type):
    """
    Format document output with proper sections and explanations
    """
    # Check if the document already has section headers
    has_sections = re.search(r'#{2,3}\s+\w+', document_text)
    
    if has_sections:
        return document_text
    
    # Extract document content
    formatted_text = document_text
    
    # Add document guide section
    guide_section = f"""## Document Guide
This {document_type.replace('_', ' ')} has been structured according to professional standards and best practices.

### Key Components:
- Professional formatting and structure
- Industry-standard sections
- Clear and concise language
- Proper styling and layout

### Customization Tips:
- Replace placeholder information with your specific details
- Adjust formatting to suit your specific needs
- Tailor the content to your target audience
- Consider regional and industry-specific conventions

"""
    
    return guide_section + formatted_text

def needs_deep_formatting(query):
    """
    Determine if a document request needs more detailed formatting
    """
    formatting_keywords = [
        "professional", "formal", "detailed", "comprehensive", "elaborate",
        "structured", "well-formatted", "standard", "proper", "official",
        "thorough", "complete", "advanced", "sophisticated", "extensive",
        "in-depth", "complex", "polished", "refined"
    ]
    
    query_lower = query.lower()
    
    # Check for formatting keywords
    formatting_score = sum(1 for keyword in formatting_keywords if keyword in query_lower)
    
    return formatting_score >= 2  # Need at least two indicators for deep formatting

def generate_document(query: str) -> str:
    """
    Generate a professional document based on the user query
    """
    # Detect the document type
    document_type = detect_document_type(query)
    
    # Determine if this is a follow-up request
    is_follow_up = any(kw in query.lower() for kw in [
        "previous", "context", "conversation", "earlier", "before", 
        "you said", "as discussed", "modify", "update", "improve",
        "continuing", "following up", "edit", "revise", "the document"
    ])
    
    # Determine if query needs deep formatting
    needs_formatting = needs_deep_formatting(query)
    formatting_level = "enhanced" if needs_formatting else "standard"
    
    # Common document generation instructions
    document_structure = ""
    
    # Document type-specific instructions
    document_type_instructions = {
        "cv": """
# CV/Resume Writing Guide
When creating a professional CV/Resume:

## Structure and Content
- Begin with clear contact information (name, phone, email, LinkedIn)
- Include a professional summary or objective statement (3-4 lines max)
- List work experience in reverse chronological order
- For each position, include company, title, dates, and 3-5 bullet points of achievements
- Include education section with degrees, institutions, and graduation dates
- Add relevant skills section with categorized technical and soft skills
- Optional sections: certifications, projects, publications, languages, volunteer work

## Formatting Guidelines
- Use clean, professional fonts (Arial, Calibri, Helvetica)
- Maintain consistent spacing and alignment throughout
- Use bullet points for readability
- Keep to 1-2 pages maximum
- Ensure consistent date formats
- Use bold/italics sparingly for emphasis
- Include quantifiable achievements where possible (%, $, metrics)

## Best Practices
- Tailor the resume to the specific job description
- Focus on achievements rather than responsibilities
- Use action verbs to begin bullet points
- Avoid first-person pronouns
- Ensure perfect grammar and spelling
- Use industry-specific keywords
- Save and send as PDF to maintain formatting
""",
        
        "cover_letter": """
# Cover Letter Writing Guide
When creating a professional cover letter:

## Structure and Format
- Include your contact information at the top
- Add date and recipient's contact information
- Use formal greeting (Dear Mr./Ms./Dr. LastName)
- Maintain 3-4 concise paragraphs with clear purpose
- Use professional closing (Sincerely, Best Regards)
- Add signature (if printed) or typed name

## Content Guidelines
- Opening paragraph: State position applying for and how you found it
- Middle paragraph(s): Highlight relevant skills/experience matching job requirements
- Final paragraph: Request interview and provide contact information
- Overall: Connect your experience directly to company needs

## Tone and Style
- Formal but conversational language
- Confident but not arrogant tone
- Avoid clichés and generic statements
- Address specific company values or recent news
- Show enthusiasm for the role and organization
- Keep to one page maximum
- Address to specific person when possible

## Professional Formatting
- Use standard business letter format
- Consistent margins (1 inch recommended)
- Professional font (same as resume)
- Left-aligned or justified paragraphs
- Single spacing with double space between paragraphs
""",
        
        "proposal": """
# Business/Project Proposal Writing Guide
When creating a professional proposal:

## Essential Sections
1. Executive Summary
   - Brief overview of entire proposal
   - Key points and value proposition
   - Limited to 1-2 paragraphs

2. Problem Statement
   - Clear identification of issue/opportunity
   - Impact of problem on client/stakeholder
   - Urgency and importance

3. Proposed Solution
   - Detailed description of solution
   - How it addresses the problem
   - Unique advantages of approach

4. Methodology
   - Step-by-step implementation plan
   - Timeline with milestones
   - Resources required

5. Qualifications
   - Relevant experience and expertise
   - Past success stories/case studies
   - Team capabilities

6. Budget/Costs
   - Detailed breakdown of expenses
   - Payment terms and schedule
   - Return on investment analysis

7. Conclusion with Call to Action
   - Reinforce value proposition
   - Clear next steps
   - Contact information

## Formatting Best Practices
- Professional letterhead and branding
- Consistent font and styling
- Strategic use of visuals (charts, graphs)
- Numbered sections with clear headings
- Page numbers for longer proposals
- Table of contents for proposals > 5 pages

## Persuasive Elements
- Client-centered language
- Evidence-based arguments
- Quantifiable benefits
- Anticipation of potential objections
- Testimonials or social proof
""",
        
        "notes": """
# Professional Notes Writing Guide
When creating effective professional notes:

## Structure and Organization
- Begin with date, time, meeting/event title
- List attendees/participants
- Outline clear agenda items or topics
- Use hierarchical organization (main topics, subtopics)
- Include action items, owners, and deadlines
- End with next steps or follow-up plan

## Content Best Practices
- Focus on key points, not verbatim transcription
- Use abbreviations and symbols consistently
- Capture decisions made and rationale
- Note dissenting opinions or concerns
- Record questions raised and answers provided
- Highlight important deadlines or milestones

## Formatting for Readability
- Use bullet points or numbered lists
- Implement indentation for subtopics
- Apply bold/italic for emphasis on key points
- Use headings and subheadings
- Include white space for readability
- Consider color-coding for different topics/priorities

## Professional Touches
- Clean, consistent formatting
- Proofread for clarity and errors
- Summarize key takeaways at beginning or end
- Include relevant reference documents or links
- Share notes promptly after meetings
- Use a consistent template for all notes
"""
    }
    
    # Get document-specific instructions or use generic
    document_instructions = document_type_instructions.get(document_type, """
# Professional Document Writing Guide
When creating any professional document:

## General Structure
- Begin with a clear title/heading
- Include introduction stating purpose and scope
- Organize content logically with headings and subheadings
- Use appropriate section breaks and transitions
- End with conclusion, next steps, or call to action
- Include relevant contact information

## Formatting Standards
- Consistent fonts and sizes throughout
- Professional spacing and margins
- Proper alignment and indentation
- Strategic use of bold, italic, and underline
- Headers and footers when appropriate
- Page numbers for multi-page documents

## Content Best Practices
- Clear, concise language
- Active voice when possible
- Appropriate tone for audience
- Error-free grammar and spelling
- Industry-specific terminology when relevant
- Data visualization when applicable

## Professional Elements
- Company branding when appropriate
- Proper citations for sources
- Appendices for supporting materials
- Consistent date formats
- Appropriate salutations and closings
- Digital signature when needed
""")
    
    # Set system prompt for document generation
    if formatting_level == "enhanced":
        system_prompt = f"""You are an expert professional document creator with extensive experience in business writing, formatting, and document design. You understand the nuances of different document types and their specific formatting requirements.

When creating a {document_type.replace('_', ' ')}:
- Begin with a properly formatted document title/header
- Use professional-level organization and structure
- Include all standard sections expected in this document type
- Apply proper spacing, margins, and formatting
- Use appropriate business language and tone
- Provide complete, ready-to-use content
- Format dates, numbers, and contact information consistently
- Include proper headers/footers where appropriate

{document_instructions}

Your output should be complete, properly formatted in Markdown, and ready for professional use with minimal editing needed.
"""
    else:
        system_prompt = f"""You are a professional document creator who helps users create well-structured documents with appropriate formatting.

For this {document_type.replace('_', ' ')}:
- Use clear, appropriate structure
- Include standard sections for this document type
- Use professional language and tone
- Provide organized, well-formatted content

{document_instructions}

Format your response clearly using Markdown for structure.
"""

    # Add context awareness to system prompt if follow-up request
    if is_follow_up:
        system_prompt += """
When modifying an existing document or answering follow-up questions:
- Maintain consistent formatting with previous content
- Ensure seamless integration of new content
- Preserve the existing tone and style
- Clearly explain what was changed and why
- Keep the document's original purpose in focus
"""

    # Create the user message with the query and document type
    user_message = f"Create a professional {document_type.replace('_', ' ')} based on this request: {query}"
    
    # Initialize the Groq client
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    try:
        # Generate document using the language model
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,  # Lower temperature for more predictable document formatting
            max_tokens=4000
        )
        
        document_response = response.choices[0].message.content
        
        # Process the response to ensure document is properly formatted
        structured_document = structure_document_output(document_response, document_type)
        
        return structured_document
    except Exception as e:
        return f"Error generating document: {str(e)}"

def detect_document_sections(document_text):
    """
    Analyze a document text to identify its main sections
    """
    # Common section patterns
    section_patterns = {
        "heading": r'^\s*#\s+(.+)$',
        "subheading": r'^\s*#{2,3}\s+(.+)$',
        "list_item": r'^\s*[\*\-\+]\s+(.+)$',
        "numbered_item": r'^\s*\d+\.\s+(.+)$',
        "paragraph": r'^([A-Z].{10,})$',
        "contact_info": r'^\s*(Email|Phone|Address|Tel|Contact):\s*(.+)$',
        "date": r'^\s*(Date|Created|Modified|Effective):\s*(.+)$'
    }
    
    sections = {}
    current_section = "header"
    lines = document_text.split('\n')
    
    for i, line in enumerate(lines):
        # Check for main heading (potential section start)
        if re.match(section_patterns["heading"], line, re.MULTILINE):
            heading = re.match(section_patterns["heading"], line, re.MULTILINE).group(1)
            current_section = heading.lower().strip().replace(' ', '_')
            if current_section not in sections:
                sections[current_section] = []
        
        # Check for subheadings
        elif re.match(section_patterns["subheading"], line, re.MULTILINE):
            subheading = re.match(section_patterns["subheading"], line, re.MULTILINE).group(1)
            subsection = subheading.lower().strip().replace(' ', '_')
            current_section = f"{current_section}_{subsection}"
            if current_section not in sections:
                sections[current_section] = []
        
        # Add content to current section
        if current_section in sections:
            sections[current_section].append(line)
    
    return sections

# Example usage
if __name__ == "__main__":
    user_query = input("What document would you like me to create? ")
    if is_document_request(user_query):
        print(generate_document(user_query))
    else:
        print("Not a document request.")
