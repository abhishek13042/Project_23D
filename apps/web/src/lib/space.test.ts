import { describe, expect, it } from "vitest";
import { checkFileName, parseSpaceError } from "./space";

describe("Space errors", () => {
  it("reads the code from every form the client uses", () => {
    expect(parseSpaceError(new Error("QUOTA_EXCEEDED: Daily limit reached."))).toEqual({
      code: "QUOTA_EXCEEDED",
      message: "Daily limit reached.",
    });
    expect(parseSpaceError({ message: "BUSY: Try again soon." }).code).toBe("BUSY");
    expect(parseSpaceError("INVALID_INPUT: Not a scan.").code).toBe("INVALID_INPUT");
  });

  it("never shows an unknown error's text", () => {
    const failure = parseSpaceError(new Error("Traceback: /home/user/app.py line 12"));
    expect(failure.code).toBe("FAILED");
    expect(failure.message).not.toContain("Traceback");
    expect(parseSpaceError(null).code).toBe("FAILED");
  });
});

describe("file names", () => {
  it("accepts NIfTI only", () => {
    expect(checkFileName("scan.nii.gz")).toBeNull();
    expect(checkFileName("SCAN.NII")).toBeNull();
    expect(checkFileName("scan.dcm")).toMatch(/NIfTI/);
  });
});
