import re
import unicodedata

class TitleNormalizer:
    """
    Cleans and normalizes raw source titles to remove marketplace noise, 
    promotional text, and standardize formatting for better matching.
    """
    
    NOISE_PATTERNS = [
        # Common promotional brackets and contents
        r'【.*?】', r'\[.*?\]', r'\(.*?\)', r'＜.*?＞', r'《.*?》',
        
        # Shipping and condition noise
        r'送料無料', r'匿名配送', r'即購入[O0]K', r'早い者勝ち', 
        r'新品', r'中古', r'美品', r'未使用', r'ジャンク', r'稼働品',
        r'未開封', r'限定', r'レア', r'激レア', r'希少', r'おまけ付き?',
        
        # Seller specific noise
        r'専用', r'セット売り', r'まとめ売り', r'バラ売り不可',
        r'値下げ不可', r'値下不可', r'最終値下げ', r'処分',
        
        # Common emoji and symbol blocks
        r'[⭐★☆✨〇◎◆◇■□△▽▲▼]',
    ]
    
    def __init__(self):
        self._compiled_noise_patterns = [re.compile(p, re.IGNORECASE) for p in self.NOISE_PATTERNS]
    
    def normalize(self, raw_title: str) -> str:
        """
        Normalizes a raw title into a clean, canonical format.
        """
        if not raw_title:
            return ""
            
        # 1. Full-width to half-width conversion for alphanumerics and spaces
        title = unicodedata.normalize('NFKC', raw_title)
        
        # 2. Remove noise patterns
        for pattern in self._compiled_noise_patterns:
            title = pattern.sub(' ', title)
            
        # 3. Standardize case (uppercase for consistent matching)
        title = title.upper()
        
        # 4. Standardize symbols (replace commas, hyphens with spaces to prevent stuck words)
        # Note: We keep hyphens if they are part of model numbers, but for title search, 
        # spaces are safer. Let's just compress multiple spaces for now.
        title = re.sub(r'[、。，．・]', ' ', title)
        
        # 5. Compress multiple whitespace and trim
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
