# PRINTBENCH NTAG216 Test Tag

Purpose: deterministic, standard NFC Forum Type 2 test tag for AMS/RFID diagnostics.

Write one **Text/NDEF** record with exactly the contents from `ntag216_test_payload.txt`.

The payload is intentionally distinctive so raw RFID/bus captures can be searched for the ASCII marker and its hex representation. It is **not** a Bambu tag clone and contains no proprietary keys or signatures.

Expected marker: `55AA33CCF00F9696`

After writing, verify the tag with an NFC reader app and keep it unlocked/read-write for diagnostics.
