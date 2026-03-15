import json

raw_text = """__Secure-1PAPISID	xarMyhGr5VxHe719/ATc3IOXP-_oAxvmKO	.google.com	/	2027-03-28T02:55:13.311Z	51		✓				High	
__Secure-1PSID	g.a0007Ahc1pXpuXjd7Bl7W-cX_e04WA5xXVdDkb_otNubw_dYf5OfHcBLOSydnaqpjuYUt1c_DAACgYKAdcSARASFQHGX2MixG6rTKSEaQztggu8CqiRYxoVAUF8yKoD72vD4sx_wCEbBfdVgryD0076	.google.com	/	2027-03-28T02:55:13.616Z	167	✓	✓				High	
__Secure-1PSIDCC	AKEyXzU-YDyb4jmdvDvEGWQqEA8RspxzYCTCDqQtf_q3gFmJO7hEW0dlZmxxY86qb7CSctuqCw	.google.com	/	2027-02-21T08:37:09.397Z	90	✓	✓				High	
__Secure-1PSIDRTS	sidts-CjYBBj1CYvHELf_vS_G2D1qv2k8taFOPjFuGQE6S3HNCKCIefWfIHy_8jeW2cQsGZNeUzDv2Gn0QAA	.google.com	/	2026-02-21T08:41:59.879Z	101	✓	✓				High	
__Secure-1PSIDTS	sidts-CjYBBj1CYvHELf_vS_G2D1qv2k8taFOPjFuGQE6S3HNCKCIefWfIHy_8jeW2cQsGZNeUzDv2Gn0QAA	.google.com	/	2027-02-21T08:31:59.879Z	100	✓	✓				High	
__Secure-3PAPISID	xarMyhGr5VxHe719/ATc3IOXP-_oAxvmKO	.google.com	/	2027-03-28T02:55:13.311Z	51		✓	None			High	
__Secure-3PSID	g.a0007Ahc1pXpuXjd7Bl7W-cX_e04WA5xXVdDkb_otNubw_dYf5Ofb9eGET900D5dJxx2alVxoAACgYKAXoSARASFQHGX2Mii8J0YOKlF5hMpbdjrJZD9xoVAUF8yKpexaoZegV1Fo1h4ZMdaCY40076	.google.com	/	2027-03-28T02:55:13.616Z	167	✓	✓	None			High	
__Secure-3PSIDCC	AKEyXzU3Aodt-VnJDR9s2T0b8-nq2Oo76MPkXrz41gZd9dSCSZqoJhsywHwdlreGdyQRLdmBgcE	.google.com	/	2027-02-21T08:37:09.397Z	91	✓	✓	None			High	
__Secure-3PSIDRTS	sidts-CjYBBj1CYvHELf_vS_G2D1qv2k8taFOPjFuGQE6S3HNCKCIefWfIHy_8jeW2cQsGZNeUzDv2Gn0QAA	.google.com	/	2026-02-21T08:41:59.880Z	101	✓	✓	None			High	
__Secure-3PSIDTS	sidts-CjYBBj1CYvHELf_vS_G2D1qv2k8taFOPjFuGQE6S3HNCKCIefWfIHy_8jeW2cQsGZNeUzDv2Gn0QAA	.google.com	/	2027-02-21T08:31:59.880Z	100	✓	✓	None			High	
__Secure-BUCKET	CMwF	.google.com	/	2026-08-20T08:10:52.321Z	19	✓	✓				Medium	
__Secure-OSID	g.a0007Ahc1un4naXq4_m1WoKyTwOhoWYypMZePiG_o0ygWyyw7q8xi0I5CDVq0HgNi6VOv1biMwACgYKAfASARASFQHGX2MiZ5E-790ypmjvzxFWX3osURoVAUF8yKrYKZ5prM4sFTEI5z6TwhH_0076	notebooklm.google.com	/	2027-03-28T02:55:13.494Z	166	✓	✓				Medium	
_ga	GA1.1.96169563.1771642515	.notebooklm.google.com	/	2027-03-28T08:31:04.214Z	28						Medium	
_ga_W0LDH41ZCB	GS2.1.s1771660004$o2$g1$t1771662664$j60$l0$h0	.notebooklm.google.com	/	2027-03-28T08:31:04.755Z	59						Medium	
_gcl_au	1.1.1973295992.1771642515	.notebooklm.google.com	/	2026-05-22T02:55:15.000Z	32						Medium	
AEC	AaJma5sNDHuRBmnnZfB-AIfjqrNWHNeZf5jE5dwuR9pFw2OLqfFVvPVXvUE	.google.com	/	2026-08-20T08:10:52.321Z	62	✓	✓	Lax			Medium	
APISID	kAJFEBoBFfFjdhDw/A1wwvXNDZFSCufEJw	.google.com	/	2027-03-28T02:55:13.311Z	40						High	
HSID	AXLSPOrlGG5teNdFa	.google.com	/	2027-03-28T02:55:13.311Z	21	✓					High	
NID	529=dW1yFyy7dph45EGuUnqSe5TdKtI2ZTeNXzBDG7y7oMyNbPw_qAeAVz0b3DcAXdPwHv6hz-7WBCVgIPv_X25JoOh_fZU1RKduam1dX_Cp7yhRlqQ6ZCJZtSc9ERkIpr_zvvOrLkDxlynhb7_4EXBO7CXqiBbyaM_IRLny-7SxN_hA0bE_uEGzzIvrO6pVrcFu9hiZFmqnjznK31LE92FmE58HupZEP2OdNcIsJkaTS3b0xkCtAOS_93j5rGeYh9K0wTatfmnjBd3Y90RP0zPJvx4A1gr7Ws53IRTOz5zXbpRghkoaYTdxfkC9KwCEPT_iyPaBHQPmv7im8vH3Q8oq5dt2k1flYhwPxFPU7dGAQG73MLJmeKDWOSwDERMhIRMWn1n3dGxNkE-OKlRQIzGjCg6LVvMpxTvYouuRCDgXdhfd1fovmhh9gHtxYKi4SoHJypROshoWSEfmYFT2OGNdoea7dCPQV_uTKlmy-l2v9NQPLqXrRSvZqHTUNqNwSA8RwYea7Ivxgoux0p_f3DD5cwQ0-RopTLrqNoE1UMlv-RHgiBGvVK0xc7GsoNuc5ZDr4A1Yy8ckKTbsB04GeqDks_ht2gOaQ4dfPT_8cn1jc7m8qtXtbo90Gd8_IM_5ql9Dp6U2YPyi-ccnsbCYx4ou4aJWDuOH3BOWSaJDMCpR5XH3ckTG11rjIvkA5Wq_QIq56-RACT8KU0CFYY5x1NqJFjVKOsk	.google.com	/	2026-08-23T02:54:18.414Z	738	✓	✓	None			Medium	
OSID	g.a0007Ahc1un4naXq4_m1WoKyTwOhoWYypMZePiG_o0ygWyyw7q8xhosxqVASRNzbDkfHGSoqEgACgYKARQSARASFQHGX2MitNpyVC-FgbjBkFQZSabnOhoVAUF8yKoBw2qUlSJDh3gOWQ46z8tp0076	notebooklm.google.com	/	2027-03-28T02:55:13.494Z	157	✓	✓				Medium	
SAPISID	xarMyhGr5VxHe719/ATc3IOXP-_oAxvmKO	.google.com	/	2027-03-28T02:55:13.311Z	41		✓				High	
SEARCH_SAMESITE	CgQImaAB	.google.com	/	2026-08-20T08:10:52.321Z	23			Strict			Medium	"""

cookies = []
for line in raw_text.strip().split('\n'):
    parts = line.split('\t')
    if len(parts) >= 4:
        name = parts[0].strip()
        value = parts[1].strip()
        domain = parts[2].strip()
        path = parts[3].strip()
        cookies.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": path,
            "secure": True
        })

with open('auth_state.json', 'w') as f:
    json.dump(cookies, f, indent=4)
print("Saved auth_state.json")
