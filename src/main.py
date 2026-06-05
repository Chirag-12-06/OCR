for image in raw:

    cleaned = preprocess(image)

    text = run_ocr(cleaned)

    json_data = extract_receipt_data(text)

    save(json_data)