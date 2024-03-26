from unidecode import unidecode
import re
from collections import defaultdict

def remove_extra_spaces(string):
    string = string.strip()
    modified_string = re.sub(r'\s+', ' ', string)
    return modified_string

def standardize_name(name):
    name = name.lower()
    name = unidecode(name)
    name = remove_extra_spaces(name)
    
    return name


# Código adaptado de: https://www.guyrutenberg.com/2008/12/15/damerau-levenshtein-distance-in-python/
# Guy Rutenberg
def damerau_levenshtein_distance_func(s1, s2):
    len_s1 = len(s1)
    len_s2 = len(s2)
    d = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

    for i in range(len_s1 + 1):
        d[i][0] = i
    for j in range(len_s2 + 1):
        d[0][j] = j

    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,  # deletion
                d[i][j - 1] + 1,  # insertion
                d[i - 1][j - 1] + cost,  # substitution
            )
            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)  # transposition
    
    distancia_final = d[len_s1][len_s2]
    distancia_normalizada = 1 - distancia_final/max(len(s1), len(s2))
    
    return distancia_normalizada

def jaccard_similarity_func(name1, name2):
    words1 = name1.split()
    words2 = name2.split()

    intersection = set(words1) & set(words2)
    union = set(words1) | set(words2)

    similarity = len(intersection)/len(union)
    
    return similarity

def most_similar_name(name1, names2):
    max_similarity = 0
    name_max_similarity = ""
    for name2 in names2:
        damerau_levenshtein_distance = damerau_levenshtein_distance_func(standardize_name(name1), standardize_name(name2))
        jaccard_similarity = jaccard_similarity_func(standardize_name(name1), standardize_name(name2))
        
        similarity = damerau_levenshtein_distance*0.5 + jaccard_similarity*0.5
        
        if similarity > max_similarity:
            max_similarity = similarity
            name_max_similarity = name2
    
    return name_max_similarity, max_similarity

def match_names(names1, names2):
    matches = defaultdict(list)
    for name1 in names1:
        if name1 not in names2:
            
            name_max_similarity, max_similarity = most_similar_name(name1, names2)
            matches[name1].append((name_max_similarity, max_similarity))
#             print(f"Match for {name1} is {name_max_similarity} with a similarity of: {max_similarity}\n\n")
        else:
            matches[name1].append((name1, 1.0))
            
    return matches