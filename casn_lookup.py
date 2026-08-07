casn = {
    '75-07-0': ['Acetaldehyde', 'Acetic aldehyde', 'Ethanal', 'Ethyl aldehyde', 'NSC 7594'],
    '53-96-3': ['Acetamide, N-9H-fluoren-2-yl-', 'Acetamide, N-Fluoren-2-yl-', 'N-9H-Fluoren-2-ylacetamide', '2-AAF', '2-Acetamidofluorene', 'FAA', 'N-2-Fluorenylacetamide', '2-FAA', '2-(Acetylamino)fluorene', 'NSC 12279'],
    '79-06-1': ['2-Propenamide', 'Acrylamide', 'Acrylic amide', 'Propenamide', 'Ethylenecarboxamide', 'Vinyl amide', 'Bio-Acrylamide 50', 'NSC 7785', 'DM 206', 'A 108465', 'Aladdin A 108467', '2-Propenamide, olymer with graphene, graft'],
    '107-13-1': ['2-Propenenitrile', 'Acrylonitrile', 'Acrylon', 'Carbacryl', 'Cyanoethylene', 'Fumigrain', 'Propenenitrile', 'VCN', 'Vinyl cyanide', 'Ventox', 'Cyanoethene', 'NSC 6362'],
    '107-repeat': ['fake', 'unknown', 'other', 'Acrylon', 'redundancy']
}

def casn_search(analyte):
    if analyte.lower() in casn:
        return analyte
    poss_casn = [key for key, val in casn.items() if analyte in val]
    if len(poss_casn) == 0:
        raise FileNotFoundError
    else:
        return poss_casn

while True:
    x = input('search analyte: ')
    if x.lower() == 'exit':
        break
    try:
        print(casn_search(x))
    except FileNotFoundError:
        print('analyte not found')