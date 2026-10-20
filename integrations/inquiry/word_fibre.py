"""The declared RR61 current choice family; no future path search."""

def first_return(word):
    if type(word) is not str or not word or word[0]!='H' or set(word)-{'H','S'}:return False
    height=0
    for i,symbol in enumerate(word):
        height+=1 if symbol=='H' else -1
        if i<len(word)-1 and height<=0:return False
    return height==0


def accepts_future_parity(word):
    return first_return(word) and word.count("H")%2==1
