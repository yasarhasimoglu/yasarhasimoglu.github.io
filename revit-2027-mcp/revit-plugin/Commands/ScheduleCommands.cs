using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitMcpPlugin.Commands
{
    /// <summary>
    /// Tablo (schedule) oluşturur: mahal listesi, kapı tablosu veya pencere tablosu.
    /// İlgili kategoriye uygun alanları otomatik ekler.
    /// </summary>
    public static class ScheduleCommands
    {
        public static object CreateSchedule(UIApplication app, JsonElement p)
        {
            Document doc = app.ActiveUIDocument.Document;
            string type = Util.GetString(p, "type", "rooms").ToLowerInvariant();

            BuiltInCategory bic;
            string defaultName;
            BuiltInParameter[] wanted;

            switch (type)
            {
                case "doors":
                case "kapi":
                    bic = BuiltInCategory.OST_Doors;
                    defaultName = "Kapı Tablosu";
                    wanted = new[] { BuiltInParameter.ALL_MODEL_MARK,
                        BuiltInParameter.ELEM_TYPE_PARAM, BuiltInParameter.DOOR_WIDTH,
                        BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.ALL_MODEL_TYPE_COMMENTS };
                    break;
                case "windows":
                case "pencere":
                    bic = BuiltInCategory.OST_Windows;
                    defaultName = "Pencere Tablosu";
                    wanted = new[] { BuiltInParameter.ALL_MODEL_MARK,
                        BuiltInParameter.ELEM_TYPE_PARAM, BuiltInParameter.WINDOW_WIDTH,
                        BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.ALL_MODEL_TYPE_COMMENTS };
                    break;
                default: // rooms / mahal
                    bic = BuiltInCategory.OST_Rooms;
                    defaultName = "Mahal Listesi";
                    wanted = new[] { BuiltInParameter.ROOM_NUMBER, BuiltInParameter.ROOM_NAME,
                        BuiltInParameter.ROOM_AREA, BuiltInParameter.ROOM_LEVEL_ID,
                        BuiltInParameter.ROOM_FINISH_FLOOR };
                    break;
            }

            string name = Util.GetString(p, "name", defaultName);
            var addedFields = new List<string>();
            long scheduleId;

            using (var t = new Transaction(doc, "Tablo oluştur: " + name))
            {
                t.Start();

                ViewSchedule schedule = ViewSchedule.CreateSchedule(doc, new ElementId(bic));
                try { schedule.Name = name; } catch { }

                var schedulable = schedule.Definition.GetSchedulableFields();
                foreach (var bp in wanted)
                {
                    SchedulableField sf = schedulable.FirstOrDefault(f =>
                        f.ParameterId.Value == (long)(int)bp);
                    if (sf != null)
                    {
                        ScheduleField field = schedule.Definition.AddField(sf);
                        addedFields.Add(field.GetName());
                    }
                }

                // İlk alana göre sırala.
                if (schedule.Definition.GetFieldCount() > 0)
                {
                    var sort = new ScheduleSortGroupField(schedule.Definition.GetFieldId(0));
                    schedule.Definition.AddSortGroupField(sort);
                }

                scheduleId = schedule.Id.Value;
                t.Commit();
            }

            return new { schedule_id = scheduleId, name, category = bic.ToString(),
                fields = addedFields };
        }
    }
}
