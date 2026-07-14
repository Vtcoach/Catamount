def run_diagnostics(load, validation):
    print("\n==============================")
    print("COA DIAGNOSTICS")
    print("==============================")

    overall_pass = True

    for field, passed in validation.items():
        result = "PASS" if passed else "FAIL"
        print(f"{field:<15} {result}")

        if not passed:
            overall_pass = False

    print("------------------------------")

    if overall_pass:
        print("Overall:        PASS")
    else:
        print("Overall:        FAIL")