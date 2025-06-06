import argparse
import sys
import logging
import os
from freesasa import Structure
import pkg_resources

default_bases = ["DA", "DC", "DG", "DT", "A", "C", "G", "U"]
modified_bases = ["DJ"]
standard_aa = ['ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO',
               'SER', 'THR', 'TRP', 'TYR', 'VAL']
modified_aa = ['ACE', 'ALY', 'ASH', 'CFE', 'CHX', 'CSP', 'CTN', 'CYC', 'CYF', 'CYM', 'DDZ', 'DUM', 'GLH', 'HLY', 'HYP',
               'M3L', 'MLY', 'MLZ', 'MSE', 'NEP', 'PNS', 'PTR', 'SEP', 'TOP', 'TYP', 'TYS']  # , 'THP'='TOP'?
valid_aa = standard_aa + modified_aa
valid_bases = default_bases + modified_bases
valid_ions = ["LI", "F", "NA", "MG", "AL", "CL", "K", "CA", "V", "CR", "MN", "FE", "NI", "CO", "CU", "ZN",
              "BR", "KR", "SR", "MO", "AG", "CD", "I", "CS", "HO", "YB", "OS", "IR", "PT", "AU", "HG", "PB"]

# Taken from NACCESS
rel_asa = {
    'total':
        {
            'ALA': 107.95,
            'CYS': 134.28,
            'ASP': 140.39,
            'GLU': 172.25,
            'PHE': 199.48,
            'GLY': 80.10,
            'HIS': 182.88,
            'ILE': 175.12,
            'LYS': 200.81,
            'LEU': 178.63,
            'MET': 194.15,
            'ASN': 143.94,
            'PRO': 136.13,
            'GLN': 178.50,
            'ARG': 238.76,
            'SER': 116.50,
            'THR': 139.27,
            'VAL': 151.44,
            'TRP': 249.36,
            'TYR': 212.76,
            'ASH': 140.39,
            'DDZ': 107.95,
            'GLH': 172.25,
            'CYM': 134.28,
            'CSP': 134.28,
            'CYF': 134.28,
            'CYC': 134.28,
            'CFE': 134.28,
            'NEP': 182.88,
            'ALY': 200.81,
            'MLZ': 200.81,
            'MLY': 200.81,
            'M3L': 200.81,
            'HYP': 136.13,
            'SEP': 116.50,
            'TOP': 139.27,
            'TYP': 212.76,
            'PTR': 212.76,
            'TYS': 212.76,
            'PNS': 116.50,
            },
    'bb':
        {
            'ALA': 38.54,
            'CYS': 37.53,
            'ASP': 37.70,
            'GLU': 37.51,
            'PHE': 35.37,
            'GLY': 47.77,
            'HIS': 35.80,
            'ILE': 37.16,
            'LYS': 37.51,
            'LEU': 37.51,
            'MET': 37.51,
            'ASN': 37.70,
            'PRO': 16.23,
            'GLN': 37.51,
            'ARG': 37.51,
            'SER': 38.40,
            'THR': 37.57,
            'VAL': 37.16,
            'TRP': 38.10,
            'TYR': 35.38,
            'ASH': 37.70,
            'DDZ': 38.54,
            'GLH': 37.51,
            'CYM': 37.53,
            'CYC': 37.53,
            'CSP': 37.53,
            'CYF': 37.53,
            'CFE': 37.53,
            'NEP': 35.80,
            'ALY': 37.51,
            'MLZ': 37.51,
            'MLY': 37.51,
            'M3L': 37.51,
            'HYP': 16.23,
            'SEP': 38.40,
            'TOP': 37.57,
            'TYP': 35.38,
            'PTR': 35.38,
            'TYS': 35.38,
            'PNS': 38.40,
            },
    'sc':
        {
            'ALA': 69.41,
            'CYS': 96.75,
            'ASP': 102.69,
            'GLU': 134.74,
            'PHE': 164.11,
            'GLY': 32.33,
            'HIS': 147.08,
            'ILE': 137.96,
            'LYS': 163.30,
            'LEU': 141.12,
            'MET': 156.64,
            'ASN': 106.24,
            'PRO': 119.90,
            'GLN': 140.99,
            'ARG': 201.25,
            'SER': 78.11,
            'THR': 101.70,
            'VAL': 114.28,
            'TRP': 211.26,
            'TYR': 177.38,
            'ASH': 102.69,
            'DDZ': 69.41,
            'GLH': 134.74,
            'CYM': 96.75,
            'CYC': 96.75,
            'CSP': 96.75,
            'CYF': 96.75,
            'CFE': 96.75,
            'NEP': 147.08,
            'ALY': 163.30,
            'MLZ': 163.30,
            'MLY': 163.30,
            'M3L': 163.30,
            'HYP': 119.90,
            'SEP': 78.11,
            'TOP': 101.70,
            'TYP': 177.38,
            'PTR': 177.38,
            'TYS': 177.38,
            'PNS': 78.11,
            }
    }


def get_accessibility(pdb_f):
    """Calls `FreeSASA <https://freesasa.github.io/>`_ using its Python API and returns per-residue accessibility
    values."""
    naccess_unsupported_aa = ['HEC', 'TIP', 'ACE', 'THP', 'HEB', 'CTN']
    logging.info("Calculate accessibility...")
    try:
        from freesasa import Classifier, structureFromBioPDB, calc
    except ImportError as err:
        print('[!] The binding affinity prediction tools require the \'freesasa\' Python API', file=sys.stderr)
        raise ImportError(err)

    asa_data, rsa_data, rel_main_chain, rel_side_chain = {}, {}, {}, {}
    _rsa = rel_asa['total']
    _rsa_bb = rel_asa['bb']
    _rsa_sc = rel_asa['sc']

    # Workaround to get relative accessibility values for Nucleic Acids (will always be accessible)
    for na in valid_bases:
        _rsa[na] = 1
        _rsa_bb[na] = 1
        _rsa_sc[na] = 1

    config_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + '/naccess.config'
    classifier = Classifier(config_path)
    pkg_resources.cleanup_resources()

    struct = Structure(pdb_f, classifier, options={})
    struct.setRadiiWithClassifier(classifier)
    result = calc(struct)

    # iterate over all atoms to get SASA and residue name
    for idx in range(struct.nAtoms()):
        atname = struct.atomName(idx).strip()
        resname = struct.residueName(idx).strip()
        resid = int(struct.residueNumber(idx))
        chain = struct.chainLabel(idx)
        at_uid = (chain, resname, resid, atname)
        res_uid = (chain, resname, resid)

        asa = result.atomArea(idx)
        asa_data[at_uid] = asa
        # add asa to residue
        rsa_data[res_uid] = rsa_data.get(res_uid, 0) + asa

        # If residue name is unknown, this is probably an ion, set a relative accessibility of -1
        if resname not in _rsa and (resname not in valid_aa + valid_bases or resname[:2] in valid_ions
                                    or resname in naccess_unsupported_aa):
            logging.warning(f"UPDATED RSA for {resname}")
            _rsa[resname] = -1
            _rsa_bb[resname] = -1
            _rsa_sc[resname] = -1

        # 3 cases: Regular amino-acid, regular nucleic acid, ion
        if (resname not in valid_bases and atname in ('C', 'N', 'O')) or \
                (resname in valid_bases and atname in ('P', 'C1', 'C9')):
            rel_main_chain[res_uid] = rel_main_chain.get(res_uid, 0) + asa
        elif resname not in valid_aa + valid_bases and resname[:2] in valid_ions:
            rel_main_chain[res_uid] = rel_main_chain.get(res_uid, 0) + asa
            rel_side_chain[res_uid] = rel_side_chain.get(res_uid, 0) + asa
        else:
            rel_side_chain[res_uid] = rel_side_chain.get(res_uid, 0) + asa
    # convert total asa ro relative asa
    rsa_data.update((res_uid, asa / _rsa[res_uid[1]]) for res_uid, asa in rsa_data.items())
    rel_main_chain.update((res_uid, asa / _rsa_bb[res_uid[1]] * 100) for res_uid, asa in rel_main_chain.items())
    rel_side_chain.update((res_uid, asa / _rsa_sc[res_uid[1]] * 100) for res_uid, asa in rel_side_chain.items())
    # We format to fit the pipeline
    resid_access = {}
    for res_uid, access in rel_main_chain.items():
        chain = res_uid[0]
        # resname = res_uid[1]
        resnum = res_uid[2]
        if chain not in resid_access:
            resid_access[chain] = {}
        resid_access[chain][resnum] = {'side_chain_rel': rel_side_chain.get(res_uid, 0), 'main_chain_rel': access}
    for chain in resid_access:
        logging.info(f"Chain: {chain} - {len(resid_access[chain])} residues")
    return resid_access


def apply_cutoff(access_data, cutoff):
    """Apply a cutoff to the sidechain relative accessibility and display on stdout"""
    logging.info(f'Applying cutoff to side_chain_rel - {cutoff}')
    for chain in access_data:
        result_list = []
        for res in access_data[chain]:
            sidechain_relative_accessibility = access_data[chain][res]['side_chain_rel']
            if sidechain_relative_accessibility >= cutoff * 100:
                result_list.append(res)
        result_list = list(set(result_list))
        result_list.sort()
        result_str = ','.join(map(str, result_list))
        logging.info(f'Chain {chain} - {result_str}')

import PyPluMA
import PyIO
class CalcAccessibilityPlugin:
    def input(self, inputfile):
        self.parameters = PyIO.readParameters(inputfile)
    def run(self):
        pass
    def output(self, outputfile):
       #if __name__ == "__main__":
       #parser = argparse.ArgumentParser()
       #levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
       #parser.add_argument('--log-level', default='INFO', choices=levels)
       #parser.add_argument('--cutoff', default=0.4, type=float, help='Relative cutoff for sidechain accessibility')
       #parser.add_argument("pdb_input", help='PDB structure')

       #args = parser.parse_args()

       logging.basicConfig(level='INFO',
                           format='%(asctime)s L%(lineno)d %(levelname)s - %(message)s',
                           datefmt='%d/%m/%Y %H:%M:%S')

       pdb_input = PyPluMA.prefix()+"/"+self.parameters["pdbfile"]
       access_dic = get_accessibility(pdb_input)
       cutoff = float(self.parameters["cutoff"])
       apply_cutoff(access_dic, cutoff)
