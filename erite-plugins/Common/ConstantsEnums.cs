using System;

namespace EritePlugins.Common
{
   public static class Enums
   {
   }

   public static class Consts
   {
      public static class PluginNames
      {
         public const string GeneratorPluginName = "Purulaatikkogeneraattori";
      }
   }

    public static class EnumConverter
    {
        public static T TryFromInt<T>(int value, T defaultValue) where T : struct, IConvertible
        {
            Type type = typeof(T);
            if (Enum.IsDefined(type, value))
            {
                return (T)Enum.Parse(type, value.ToString());
            }
            return defaultValue;
        }
    }
}
