// Trainer API keeps shifts as a list: [{ weekday, start_time, end_time }]
export const shiftsToWeek = (shifts) =>
  Object.fromEntries(
    shifts.map((s) => [String(s.weekday), [s.start_time.slice(0, 5), s.end_time.slice(0, 5)]]),
  );

export const weekToShifts = (week) =>
  Object.entries(week).map(([day, [start, end]]) => ({
    weekday: Number(day),
    start_time: start,
    end_time: end,
  }));
