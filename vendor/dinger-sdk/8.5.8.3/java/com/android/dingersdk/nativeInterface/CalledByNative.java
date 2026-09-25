package com.android.dingersdk.nativeInterface;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target({ElementType.CONSTRUCTOR, ElementType.METHOD})
@Retention(RetentionPolicy.CLASS)
/* Source: official 8.5.8.3 base.apk/classes27.dex; decompiled with JADX. */
public @interface CalledByNative {
    String value() default "";
}
