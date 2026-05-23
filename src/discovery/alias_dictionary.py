from typing import Dict, List, Optional
import re

class AliasDictionary:
    """
    Applies persistent normalization dictionaries to incoming raw source items.
    Improves normalization quality without forcing hard merges.
    """
    
    def __init__(self, alias_repo):
        self.repo = alias_repo
        self._brand_aliases: Dict[str, str] = {}
        self._model_aliases: Dict[str, str] = {}
        self._mpn_normalization_rules: List[Dict[str, str]] = []
        self._source_noise_tokens: Dict[str, List[str]] = {}
        self._is_loaded = False
        
    def load_dictionaries(self):
        """Loads enabled aliases from the persistent repository."""
        aliases = self.repo.get_all_enabled_aliases()
        
        self._brand_aliases.clear()
        self._model_aliases.clear()
        self._mpn_normalization_rules.clear()
        self._source_noise_tokens.clear()
        
        for alias in aliases:
            if alias.alias_type == "brand":
                self._brand_aliases[alias.token.lower()] = alias.resolution
            elif alias.alias_type == "model":
                self._model_aliases[alias.token.lower()] = alias.resolution
            elif alias.alias_type == "mpn_rule":
                # mpn_rule could be a regex pattern replacement
                self._mpn_normalization_rules.append({
                    "pattern": alias.token,
                    "replacement": alias.resolution
                })
            elif alias.alias_type == "noise":
                # Token could be "rakuten", resolution could be empty ""
                # Or specific to a source_platform
                platform = alias.source_platform or "global"
                if platform not in self._source_noise_tokens:
                    self._source_noise_tokens[platform] = []
                self._source_noise_tokens[platform].append(alias.token)
                
        self._is_loaded = True

    def resolve_brand(self, raw_brand: Optional[str]) -> Optional[str]:
        if not raw_brand:
            return None
        if not self._is_loaded:
            self.load_dictionaries()
            
        lower_brand = raw_brand.lower().strip()
        return self._brand_aliases.get(lower_brand, raw_brand)
        
    def resolve_model(self, raw_model: Optional[str]) -> Optional[str]:
        if not raw_model:
            return None
        if not self._is_loaded:
            self.load_dictionaries()
            
        lower_model = raw_model.lower().strip()
        return self._model_aliases.get(lower_model, raw_model)
        
    def resolve_mpn(self, raw_mpn: Optional[str]) -> Optional[str]:
        if not raw_mpn:
            return None
        if not self._is_loaded:
            self.load_dictionaries()
            
        resolved = raw_mpn
        for rule in self._mpn_normalization_rules:
            pattern = rule["pattern"]
            replacement = rule["replacement"]
            try:
                resolved = re.sub(pattern, replacement, resolved)
            except re.error:
                continue
                
        return resolved

    def strip_source_noise(self, title: str, source_platform: str) -> str:
        """Removes source-specific noise tokens from the raw title."""
        if not title:
            return ""
        if not self._is_loaded:
            self.load_dictionaries()
            
        noise_tokens = []
        noise_tokens.extend(self._source_noise_tokens.get("global", []))
        if source_platform:
            noise_tokens.extend(self._source_noise_tokens.get(source_platform, []))
            
        clean_title = title
        for token in noise_tokens:
            # Simple replace. Could be improved with regex boundary matches if needed.
            clean_title = re.sub(rf'(?i)\b{re.escape(token)}\b', '', clean_title)
            
        # Clean up double spaces resulting from removals
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        return clean_title
