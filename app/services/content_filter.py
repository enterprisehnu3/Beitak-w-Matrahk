import re

BAD_WORDS = [
    'كسمك', 'كس امك', 'شرموط', 'خول', 'عرص', 'منيوك', 'لبوة', 'متناكة', 'قحبة', 'سكس',
    'sex', 'porn', 'fuck', 'shit', 'asshole', 'bitch'
]

def filter_message(content):
    """
    Filters a message content for bad words and patterns.
    Returns (filtered_content, was_modified).
    """
    if not content:
        return content, False
        
    was_modified = False
    filtered_content = content
    
    # 1. Filter Bad Words
    for word in BAD_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        if pattern.search(filtered_content):
            filtered_content = pattern.sub('*' * len(word), filtered_content)
            was_modified = True
            
    # 2. Filter Phone Numbers (Egyptian format)
    phone_pattern = r'(01[0125][0-9]{8})'
    if re.search(phone_pattern, filtered_content):
        filtered_content = re.sub(phone_pattern, '[PHONE HIDDEN]', filtered_content)
        was_modified = True
        
    return filtered_content, was_modified
