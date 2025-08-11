import re
import pykew.powo as powo
from pykew.powo_terms import Name, Filters

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text)

def flatten_object(
        obj, level = 0, clean = True, include_tags = None, exclude_tags = None,
        keywords = None
        ):
    """
    Flatten a nested object into a string representation.
    
    Parameters
    ----------
    obj : dict | list | str
        The object to flatten.
    level : int
        The current level of nesting (used for indentation).
    clean : bool
        Whether to remove HTML tags from the flattened output.
    include_tags : list
        A list of tags to include in the flattened output.
        Supports regular expressions.
    exclude_tags : list
        A list of tags to exclude from the flattened output.
        Supports regular expressions.
    
    Returns
    -------
    str
        The flattened string representation of the object.
    """
    def matches_any(key, patterns):
        for pattern in patterns:
            if not pattern:
                continue
            if re.search(pattern, key, re.IGNORECASE):
                return True
        return False
    
    def has_include_tag(obj, patterns):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if matches_any(k, patterns):
                    return True
                if has_include_tag(v, patterns):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if has_include_tag(item, patterns):
                    return True
        return False
    
    if include_tags is None:
        include_tags = []
    if exclude_tags is None:
        exclude_tags = []
    
    if isinstance(obj, str):
        return strip_html(obj) if clean else obj
    
    if isinstance(obj, dict):
        if include_tags and has_include_tag(obj, include_tags):
            return flatten_object(
                obj, level, clean, include_tags = None,
                exclude_tags = exclude_tags
                )
        
        parts = []
        for k, v in obj.items():
            if matches_any(k, exclude_tags):
                continue
            if include_tags and not matches_any(k, include_tags):
                continue
            parts.append(
                f"{k}: {flatten_object(
                    v, level + 1, clean, include_tags, exclude_tags
                    )}"
                )
        return "\n".join(parts)

    if isinstance(obj, list):
        return "\n".join(
            flatten_object(
                v, level + 1, clean, include_tags, exclude_tags
                ) for v in obj
            )
    
    text = strip_html(str(obj)) if clean else str(obj)

    if keywords:
        text = text.split("\n")
        text = [
            line.strip() for line in text if any(
                re.search(keyword, line, re.IGNORECASE) for keyword in keywords
                )
            ]
        text = "\n".join(text)
    
    return text


def get_descriptions(
        name = None, genus = None, epithet = None, flatten = True, **kwargs
        ):
    """
    Get descriptions for a plant species from kew.org.
    Either the name as a single string or both genus and epithet must be
    provided.

    Parameters
    ----------
    name : str | None
        The common name of the plant.
    genus : str | None
        The genus of the plant.
    epithet : str | None
        The species epithet of the plant.
    flatten : bool
        Whether to remove HTML tags from the flattened output.
    **kwargs : dict
        Additional keyword arguments to pass to the flatten function.
    
    Returns
    -------
    list
        A list of descriptions found in the query results.
    """
    if name:
        results = powo.search(name)
    elif genus and epithet:
        query = {Name.genus: genus, Name.species: epithet}
        results = powo.search(
            query, filters = [Filters.accepted, Filters.species]
            )
    else:
        raise ValueError(
            "Either name or both genus and epithet must be provided."
            )
    
    descriptions = []
    for result in results:
        fqid = result["fqId"]
        details = powo.lookup(fqid, include = ["descriptions"])
        description = (
            details.get("descriptions") or details.get("description") or "N/A"
        )
        descriptions.append(description)
    
    return flatten_object(descriptions, **kwargs) if flatten else descriptions

# Usage example
if __name__ == "__main__":
    description = get_descriptions(
        name = "Ceiba pentandra",
        include_tags = ["morph"],
        exclude_tags = [
            "source", "distribution", "author",
            "food", "conservation", "synonym", "vernacular",
            "usematerial", "usemedicine", "usepoison", "usesocial",
            "useenvironmental"
        ], keywords = ["flower", "leaf", "stem", "trunk", "buttress"],
        flatten = True
        )
    print(description)