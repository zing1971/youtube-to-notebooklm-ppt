import json
import subprocess

raw_text = """
__Secure-1PAPISID	xarMyhGr5VxHe719/ATc3IOXP-_oAxvmKO	.google.com	/	2027-03-28T02:55:13.311Z	51		✓				High	
__Secure-1PSID	g.a0007Ahc1pXpuXjd7Bl7W-cX_e04WA5xXVdDkb_otNubw_dYf5OfHcBLOSydnaqpjuYUt1c_DAACgYKAdcSARASFQHGX2MixG6rTKSEaQztggu8CqiRYxoVAUF8yKoD72vD4sx_wCEbBfdVgryD0076	.google.com	/	2027-03-28T02:55:13.616Z	167	✓	✓				High	
__Secure-1PSIDCC	AKEyXzVHUS-0_oR6FHR40ePQDhRiAXqDjmWX9wsswpTwv0l_hLL0GeRXjr6QZPpJOABYiDT9	.google.com	/	2027-02-21T02:59:17.692Z	88	✓	✓				High	
__Secure-1PSIDRTS	sidts-CjYBBj1CYv9cGom1qA-_eWs4OZibABPREsmlsvdNF9D5l8zqRSGLKbN12GFJVd_V42dvemsY4OoQAA	.google.com	/	2026-02-21T03:05:13.827Z	101	✓	✓				High	
__Secure-1PSIDTS	sidts-CjYBBj1CYv9cGom1qA-_eWs4OZibABPREsmlsvdNF9D5l8zqRSGLKbN12GFJVd_V42dvemsY4OoQAA	.google.com	/	2027-02-21T02:55:13.826Z	100	✓	✓				High	
__Secure-3PAPISID	xarMyhGr5VxHe719/ATc3IOXP-_oAxvmKO	.google.com	/	2027-03-28T02:55:13.311Z	51		✓	None			High	
__Secure-3PSID	g.a0007Ahc1pXpuXjd7Bl7W-cX_e04WA5xXVdDkb_otNubw_dYf5Ofb9eGET900D5dJxx2alVxoAACgYKAXoSARASFQHGX2Mii8J0YOKlF5hMpbdjrJZD9xoVAUF8yKpexaoZegV1Fo1h4ZMdaCY40076	.google.com	/	2027-03-28T02:55:13.616Z	167	✓	✓	None			High	
__Secure-3PSIDCC	AKEyXzUsd26RJDNGW1_5RSSpfev8O4b0zAkQbvMVP47a9cgeHVZvlyo7TKgc39ZpyfLz0gbnCg	.google.com	/	2027-02-21T02:59:17.692Z	90	✓	✓	None			High	
__Secure-3PSIDRTS	sidts-CjYBBj1CYv9cGom1qA-_eWs4OZibABPREsmlsvdNF9D5l8zqRSGLKbN12GFJVd_V42dvemsY4OoQAA	.google.com	/	2026-02-21T03:05:13.827Z	101	✓	✓	None			High	
__Secure-3PSIDTS	sidts-CjYBBj1CYv9cGom1qA-_eWs4OZibABPREsmlsvdNF9D5l8zqRSGLKbN12GFJVd_V42dvemsY4OoQAA	.google.com	/	2027-02-21T02:55:13.827Z	100	✓	✓	None			High	
__Secure-OSID	g.a0007Ahc1un4naXq4_m1WoKyTwOhoWYypMZePiG_o0ygWyyw7q8xi0I5CDVq0HgNi6VOv1biMwACgYKAfASARASFQHGX2MiZ5E-790ypmjvzxFWX3osURoVAUF8yKrYKZ5prM4sFTEI5z6TwhH_0076	notebooklm.google.com	/	2027-03-28T02:55:13.494Z	166	✓	✓				Medium	
_ga	GA1.1.96169563.1771642515	.notebooklm.google.com	/	2027-03-28T02:55:15.047Z	28						Medium	
_ga_W0LDH41ZCB	GS2.1.s1771642515$o1$g0$t1771642515$j60$l0$h0	.notebooklm.google.com	/	2027-03-28T02:55:15.337Z	59						Medium	
_gcl_au	1.1.1973295992.1771642515	.notebooklm.google.com	/	2026-05-22T02:55:14.000Z	32						Medium	
APISID	kAJFEBoBFfFjdhDw/A1wwvXNDZFSCufEJw	.google.com	/	2027-03-28T02:55:13.311Z	40						High	
HSID	AXLSPOrlGG5teNdFa	.google.com	/	2027-03-28T02:55:13.311Z	21	✓					High	
NID	529=QxJx04lwcWk8ZTo4iNyqyN3Fhxz5ZEReXNLyhIkJkpbWjikKkXSnJTg5E2IukxNEqGJDKmVP9nf9zqGOynDlG8K9Hn8CyB1BO3tPIDHG5CObWJ33E1zlbp2kYnyS_6DFjpstaTIz4_0ih5mEXrbTjuyRFZQnJvDjqhTfzVuUS5DlR2lYWEcXbbnlk0iwpi2Ce0UoH4vARaMGbNFvF8h65-kLAVLkCrg0pOKlZEBAhBIePhazWSNm2sybzQEQmcse8_gc8j00YAjMVs3zpj0np6rcHuLAXno8OIl9sEc3ZQcCpO5VMiQVAyvIApiycampkHyJfrPDAtys-GoPwPp6yj6YFdFw4_ocmxZpmLmoLuj5Hqna_vWiiJfI1p49mV7tF4ez2HNwS1QxjTT8dm_Np3HLmIIByFANPuO3UssrzJJ8BSfWgbGAgOKRCZWccYNaOhRw-ja3D_KreQuSC6BHTOV-of6PyMRNcFA9Ea2etammhwv0kWSd6wmXjLn9NEx56NuQacz6QgvGDTXK9E9MxlAGEUwsQxthfPQNc9R_YKWBGOfbYi6eeE8gWyMFFaHChPKjz6MorfP2duf9j1FnnPpkp3XpFvECCQrCKIOupV85Clo4XOzJY3vHnk-AHKpBigYnScydtl86-7EWoa96U7RQy4p5gwojpBpEqJGrcmgtY1qcKWkA9MjO2Obu	.google.com	/	2026-08-23T02:54:18.310Z	707	✓	✓	None			Medium	
OSID	g.a0007Ahc1un4naXq4_m1WoKyTwOhoWYypMZePiG_o0ygWyyw7q8xhosxqVASRNzbDkfHGSoqEgACgYKARQSARASFQHGX2MitNpyVC-FgbjBkFQZSabnOhoVAUF8yKoBw2qUlSJDh3gOWQ46z8tp0076	notebooklm.google.com	/	2027-03-28T02:55:13.494Z	157	✓	✓				Medium	
SAPISID	xarMyhGr5VxHe719/ATc3IOXP-_oAxvmKO	.google.com	/	2027-03-28T02:55:13.311Z	41		✓				High	
SID	g.a0007Ahc1pXpuXjd7Bl7W-cX_e04WA5xXVdDkb_otNubw_dYf5OfEQo9VeYzBoc5p-lH2HY_oQACgYKAYoSARASFQHGX2MiV8sdhPOhnlSRy3EJO7XSmRoVAUF8yKoYxktkaIbvxAD7pEywe2jT0076	.google.com	/	2027-03-28T02:55:13.616Z	156						High	
SIDCC	AKEyXzVGu-o-Kj37_hSJx5SPqAeu4qmRcdR2b9q8Xd199o2S_1n1WspnkwOGlKAcKoJD73hq	.google.com	/	2027-02-21T02:59:17.691Z	77						High	
SSID	AYYVNi4sarnV8aLsg	.google.com	/	2027-03-28T02:55:13.311Z	21	✓	✓				High	
"""

cookies = []
for line in raw_text.strip().split('\n'):
    parts = line.split('\t')
    if len(parts) >= 4:
        cookie = {
            "name": parts[0].strip(),
            "value": parts[1].strip(),
            "url": "https://notebooklm.google.com"
        }
        cookies.append(cookie)

with open("auth_state.json", "w", encoding="utf-8") as f:
    json.dump(cookies, f, indent=2, ensure_ascii=False)

print(f"成功將 {len(cookies)} 筆 Cookie 轉換為 auth_state.json。")

try:
    subprocess.run(["gh", "secret", "set", "NOTEBOOKLM_AUTH_STATE"], 
                   input=json.dumps(cookies).encode('utf-8'), check=True)
    print("✅ 成功將授權資訊上傳到 GitHub Secrets！")
except Exception as e:
    print(f"❌ 上傳 GitHub Secrets 失敗: {e}")
