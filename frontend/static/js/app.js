/* Home: shares, POST /submit-data */
const API_BASE = window.API_BASE || "";

function splitIntoThreeShares(value) {
  const v = Math.max(0, Math.floor(Number(value)));
  const s1 = Math.floor(Math.random() * (v + 1));
  const s2 = Math.floor(Math.random() * (v - s1 + 1));
  const s3 = v - s1 - s2;
  return [s1, s2, s3];
}

function getMarksFromFiveSubjects() {
  const marks = [];
  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById("subject" + i);
    const val = parseFloat(el.value);
    marks.push(Number.isNaN(val) ? 0 : Math.max(0, Math.min(10, val)));
  }
  const gradeSum = marks.reduce(function (a, b) {
    return a + b;
  }, 0);
  const gradeCount = marks.length;
  const sumScaled = Math.round(gradeSum * 100);
  const sumParts = splitIntoThreeShares(sumScaled);
  const countParts = splitIntoThreeShares(gradeCount);
  return {
    share1: { grade_sum: sumParts[0], grade_count: countParts[0] },
    share2: { grade_sum: sumParts[1], grade_count: countParts[1] },
    share3: { grade_sum: sumParts[2], grade_count: countParts[2] },
  };
}

function showFormError(msg) {
  const el = document.getElementById("form-error");
  if (!el) return;
  el.textContent = msg;
  el.hidden = !msg;
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("student-form");
  const submitBtn = document.getElementById("submit-btn");
  if (!form || !submitBtn) return;

  console.log("[portal] Home loaded, API_BASE:", API_BASE || "(same origin)");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    showFormError("");

    const studentId = document.getElementById("student-id").value.trim() || "anonymous";
    const present = parseInt(document.getElementById("present").value, 10);
    const total = parseInt(document.getElementById("total").value, 10);

    if (Number.isNaN(total) || total < 1) {
      showFormError("Total days must be at least 1.");
      console.warn("[portal] invalid total");
      return;
    }
    if (Number.isNaN(present) || present < 0 || present > total) {
      showFormError("Days present must be between 0 and total days.");
      console.warn("[portal] invalid present");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.classList.add("is-loading");

    try {
      const p = splitIntoThreeShares(present);
      const t = splitIntoThreeShares(total);
      const gradeShares = getMarksFromFiveSubjects();

      const share1 = {
        attendance_present: p[0],
        attendance_total: t[0],
        grade_sum: gradeShares.share1.grade_sum,
        grade_count: gradeShares.share1.grade_count,
      };
      const share2 = {
        attendance_present: p[1],
        attendance_total: t[1],
        grade_sum: gradeShares.share2.grade_sum,
        grade_count: gradeShares.share2.grade_count,
      };
      const share3 = {
        attendance_present: p[2],
        attendance_total: t[2],
        grade_sum: gradeShares.share3.grade_sum,
        grade_count: gradeShares.share3.grade_count,
      };

      console.log("[portal] POST /submit-data");

      const res = await fetch(API_BASE + "/submit-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: studentId,
          share1: share1,
          share2: share2,
          share3: share3,
        }),
      });

      const data = await res.json().catch(function () {
        return {};
      });
      console.log("[portal] submit-data:", res.status, data);

      if (!res.ok || data.ok === false) {
        throw new Error(data.error || "Submit failed");
      }

      if (!data.student_token) {
        throw new Error("No token returned");
      }
      sessionStorage.setItem("student_result_token", data.student_token);
      window.location.href = "/result";
    } catch (err) {
      console.error("[portal] Submit error:", err);
      showFormError(err.message || "Something went wrong.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.classList.remove("is-loading");
    }
  });
});
