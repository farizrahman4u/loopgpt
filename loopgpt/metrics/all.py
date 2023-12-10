import loopgpt
from typing import Dict, List


@loopgpt.aifunc()
def command_to_statements(command: Dict[str, str]) -> List[str]:
    """Extract statements from the given command.

    Examples:

    >>> command_to_statements({"name": "browser", "args": {"link": "https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340"}})
    ["https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340 is a website."]
    >>> command_to_statements({"name": "write_to_file", "args": {"file": "headphones.txt", "content": "Best Headphones: Sony WH-1000XM4, Bose QC35, Sennheiser HD 450BT"}})
    [
        "Sony WH-1000XM4, Bose QC35, Sennheiser HD 450BT are the best headphones.",
    ]

    >>> command_to_statements({"name": "google_search", "args": {"query": "Battle of Waterloo"}})
    []
    
    >>> command_to_statements(
    ...     {
    ...         "name": "write_to_file", 
    ...         "args": {"file": "tut.txt", "content": "King Tutankhamun was the antepenultimate pharaoh of the 18th Dynasty of ancient Egypt. His death marked the cessation of the dynasty's royal line. Tutankhamun ascended to the throne around the age of nine and reigned until his death around the age of nineteen."}
    ...     }
    ... )
    [
        "King Tutankhamun was the antepenultimate pharaoh of the 18th Dynasty of ancient Egypt.",
        "King Tutankhamun's death marked the end of the dynasty's royal line.",
        "King Tutankhamun reigned from the age of nine until his death around the age of nineteen.",
    ]
    """

@loopgpt.aifunc()
def check_statement_correctness(statements: str, context: str) -> Dict[str, str]:
    """Verify if the statements can be attributed to the given context.

    Examples:

    >>> context = '''Google search for "best headphones" returned:
    ... https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340 - The best headphones 2023: top cans from Sony, Bose and ...
    ... https://www.cnet.com/tech/mobile/best-headphones/ - Best headphones for 2023
    ... https://www.rtings.com/headphones/reviews/best/headphones - The 8 best headphones - Fall 2023: Reviews
    ... '''
    >>> check_statement_correctness("https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340 is a website.", context)
    {
        "reason": "The context directly mentions this website.",
        "verdict": "Yes",
    }
    >>> check_statement_correctness("https://www.headphonezone.in is a website.", context)
    {
        "reason": "There is no mention of headphonezone.in in the context.",
        "verdict": "No",
    }

    >>> context = '''Tutankhamun was the antepenultimate pharaoh of the Eighteenth Dynasty of ancient Egypt. His death marked the cessation of 
    ... the dynasty's royal line. Tutankhamun ascended to the throne around the age of nine and reigned until his death around the age of nineteen. 
    ... The preeminent action of his reign is the countermanding of the religiopolitical changes enacted by his predecessor, Akhenaten, during the 
    ... Amarna Period: he restored the traditional polytheistic form of ancient Egyptian religion, undoing the religious shift known as Atenism, and moved 
    ... the royal court away from Akhenaten's capital, Amarna.'''
    >>> check_statement_correctness("Tutankhamun was the antepenultimate pharaoh of the Eighteenth Dynasty of ancient Egypt.", context)
    {
        "reason": "The exact sentence is present in the context.",
        "verdict": "Yes",
    }
    >>> check_statement_correctness("Tutankhamun's reign ended with his death around the age of nineteen.", context)
    {
        "reason": "From the context it is clear that Tutankhamun reigned till his death around 19 years of age.",
        "verdict": "Yes",
    }
    >>> check_statement_correctness("Tutankhamun is also known as Tutankhaten.", context)
    {
        "reason": "There is no supporting evidence for this in the given context.",
        "verdict": "No",
    }
    """

@loopgpt.aifunc()
def command_usefulness(command: Dict[str, str], goal: str) -> Dict[str, str]:
    """Verify if the given command is useful for achieving the goal.

    Examples:

    >>> command_usefulness({"name": "browser", "args": {"url": "https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340"}}, "Find the best headphones")
    {
        "reason": "Browsing this website can be useful for finding the best headphones.",
        "verdict": "Yes",
    }
    
    >>> command_usefulness({"name": "google_search", "args": {"query": "cat videos"}}, "Find the best headphones")
    {
        "reason": "Searching google for cat videos is not useful for finding the best headphones.",
        "verdict": "No",
    }

    >>> command_usefulness({"name": "write_to_file", "args": {"file": "king_tut.txt", "content": ""}}, "I will write about King Tutankhamun")
    {
        "reason": "This command does not write anything to the file.",
        "verdict": "No",
    }

    >>> command_usefulness({"name": "browser", "args": {"url": "", "content": ""}}, "I will find details about Napoleon Bonaparte")
    {
        "reason": "This command does not open any website as no URL is provided.",
        "verdict": "No",
    }
    """

@loopgpt.aifunc()
def context_precision(goal: str, context: str) -> Dict[str, str]:
    """Verify if the information in the given context is useful for achieving the goal.

    Examples:

    >>> context = '''Google search for "best headphones" returned:
    ... https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340 - The best headphones 2023: top cans from Sony, Bose and ...
    ... https://www.cnet.com/tech/mobile/best-headphones/ - Best headphones for 2023
    ... https://www.rtings.com/headphones/reviews/best/headphones - The 8 best headphones - Fall 2023: Reviews
    ... '''
    >>> context_precision("Compare the prices of the best headphones of 2023", context)
    {
        "reason": "Although the context provides links to the best headphones, it does not provide the prices. Thus, it is not useful for comparing the prices.",
        "verdict": "No",
    }

    >>> context = '''Albert Einstein was a German-born theoretical physicist who developed the theory of relativity, one of the two pillars of modern physics (alongside quantum mechanics). His work is also known for its influence on the philosophy of science. He is best known to the general public for his mass energy equivalence formula E = mc2, which has been dubbed "the world's most famous equation". He received the 1921 Nobel Prize in Physics "for his services to theoretical physics, and especially for his discovery of the law of the photoelectric effect", a pivotal step in the development of quantum theory.'''
    >>> context_precision("Write a summary of Albert Einstein", context)
    {
        "reason": "This context is extremely useful for writing a summary of Albert Einstein as it describes his life and work.",
        "verdict": "Yes",
    }
    """

@loopgpt.aifunc()
def context_relevancy(goal: str, context: str) -> Dict[str, List[str]]:
    """Extract relevant sentences from the provided context which are absolutely essential for achieving the goal.

    Examples:

    >>> context = '''Google search for "best headphones" returned:
    ... https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340 - The best headphones 2023: top cans from Sony, Bose and ...
    ... https://www.cnet.com/tech/mobile/best-headphones/ - Best headphones for 2023
    ... https://www.rtings.com/headphones/reviews/best/headphones - The 8 best headphones - Fall 2023: Reviews
    ... '''
    >>> context_relevancy("Latest shoe trends", context)
    {
        "reason": "Nothing in the context is relevant for finding the latest shoe trends.",
        "candidate_sentences": [],
    }
    >>> context_relevancy("Best headphones of 2023", context)
    {
        "reason": "These links maybe relevant for finding the best headphones of 2023.",
        "candidate_sentences": [
            'https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340 - The best headphones 2023: top cans from Sony, Bose and ...',
            'https://www.cnet.com/tech/mobile/best-headphones/ - Best headphones for 2023',
            'https://www.rtings.com/headphones/reviews/best/headphones - The 8 best headphones - Fall 2023: Reviews',
        ]
    }
    >>> context_relevancy("Find price of Sony WH-1000XM4", context)
    {
        "reason": "These links maybe relevant for finding the price of Sony WH-1000XM4.",
        "candidate_sentences": [
            'https://www.techradar.com/news/audio/portable-audio/best-headphones-1280340 - The best headphones 2023: top cans from Sony, Bose and ...',
            'https://www.cnet.com/tech/mobile/best-headphones/ - Best headphones for 2023',
            'https://www.rtings.com/headphones/reviews/best/headphones - The 8 best headphones - Fall 2023: Reviews',
        ]
    }
    """
