from pathlib import Path
import json
TEXT='PRINTBENCH|NTAG216|CASE=A|SLOT=4|MARK=55AA33CCF00F9696|SEQ=00112233445566778899AABBCCDDEEFF|END'
lang=b'en'
text=TEXT.encode('ascii')
payload=bytes([len(lang)])+lang+text
record=bytes([0xD1,0x01,len(payload),0x54])+payload
ndef_tlv=bytes([0x03,len(record)])+record+bytes([0xFE])
out={'text':TEXT,'text_hex':text.hex().upper(),'ndef_record_hex':record.hex().upper(),'type2_tlv_hex':ndef_tlv.hex().upper(),'type2_user_memory_start_page':4,'notes':'Standard NFC Forum Type 2 NDEF Text record; no Bambu proprietary format.'}
base=Path(__file__).resolve().parent
(base/'ntag216_test_payload.txt').write_text(TEXT+'\n',encoding='ascii')
(base/'ntag216_test_payload.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
(base/'README.md').write_text('# PRINTBENCH NTAG216 Test Tag\n\nPurpose: deterministic, standard NFC Forum Type 2 test tag for AMS/RFID diagnostics.\n\nWrite one **Text/NDEF** record with exactly the contents from `ntag216_test_payload.txt`.\n\nThe payload is intentionally distinctive so raw RFID/bus captures can be searched for the ASCII marker and its hex representation. It is **not** a Bambu tag clone and contains no proprietary keys or signatures.\n\nExpected marker: `55AA33CCF00F9696`\n\nAfter writing, verify the tag with an NFC reader app and keep it unlocked/read-write for diagnostics.\n',encoding='utf-8')
print(TEXT)
print('TEXT_HEX='+text.hex().upper())
print('TLV_HEX='+ndef_tlv.hex().upper())
