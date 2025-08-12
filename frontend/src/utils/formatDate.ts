// src/utils/dateFormatter.ts
export function formatDate(date: string | Date): string {
    if (!date) return "";
    const d = new Date(date);
    if (isNaN(d.getTime())) return ""; // invalid date
    return new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    }).format(d);
}
