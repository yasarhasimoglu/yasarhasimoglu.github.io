using System;
using System.Text.Json;
using Autodesk.Revit.UI;
using RevitMcpPlugin.Commands;

namespace RevitMcpPlugin
{
    /// <summary>
    /// Komut adını ilgili işleyiciye yönlendirir. Tüm işleyiciler Revit ana
    /// iş parçacığında çalışır ve JSON'a serileştirilebilen bir nesne döner.
    /// </summary>
    public static class CommandDispatcher
    {
        public static object Dispatch(UIApplication app, string command, JsonElement p)
        {
            switch (command)
            {
                case "ping":
                    return new { pong = true, revit = app.Application.VersionNumber };

                case "get_model_info":
                    return ModelInfoCommand.GetModelInfo(app, p);

                case "set_scale_standard":
                    return ScaleStandardCommands.SetScale(app, p);

                case "create_grids":
                    return GridCommands.CreateGrids(app, p);

                case "dimension_exterior":
                    return DimensionCommands.DimensionExterior(app, p);

                case "tag_rooms":
                    return RoomTagCommands.TagRooms(app, p);

                case "create_schedule":
                    return ScheduleCommands.CreateSchedule(app, p);

                case "calculate_emsal":
                    return EmsalCommands.CalculateEmsal(app, p);

                case "calculate_total_area":
                    return EmsalCommands.CalculateTotalArea(app, p);

                default:
                    throw new InvalidOperationException("Bilinmeyen komut: " + command);
            }
        }
    }
}
