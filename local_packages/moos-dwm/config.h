/* See LICENSE file for copyright and license details. */

#include <system_state/system_state.h>
#include <status_bar/notify.h>

/* appearance */
static const unsigned int borderpx  = 0;        /* border pixel of windows */
static const unsigned int snap      = 32;       /* snap pixel */
static const int showbar            = 1;        /* 0 means no bar */
static const int topbar             = 1;        /* 0 means bottom bar */
static const char *fonts[]          = { "Hack Nerd Font Mono:size=12:antialias=true:autohint=true" };
static const char dmenufont[]       = "Hack Nerd Font Mono:size=12:antialias=true:autohint=true";
static const char col_gray1[]       = "#000000";
static const char col_gray2[]       = "#444444";
static const char col_gray3[]       = "#e5e5e5";
static const char *colors[][3]      = {
	/*               fg         bg         border   */
	[SchemeNorm] = { col_gray3, col_gray1, col_gray1 },
	[SchemeSel]  = { col_gray3, col_gray2, col_gray2 },
};

/* tagging */
static const char *tags[] = { "1", "2", "3", "4", "5" };

static const Rule rules[] = {
	/* xprop(1):
	 *	WM_CLASS(STRING) = instance, class
	 *	WM_NAME(STRING) = title
	 */
	/* class      instance    title       tags mask     isfloating   monitor */
	{ "Gimp",     NULL,       NULL,       0,            1,           -1 },
	{ "Firefox",  NULL,       NULL,       1 << 8,       0,           -1 },
};

/* layout(s) */
static const float mfact     = 0.50; /* factor of master area size [0.05..0.95] */
static const int nmaster     = 1;    /* number of clients in master area */
static const int resizehints = 1;    /* 1 means respect size hints in tiled resizals */
static const int lockfullscreen = 1; /* 1 will force focus on the fullscreen window */

static const Layout layouts[] = {
	/* symbol     arrange function */
	{ "[]=",      tile },    /* first entry is default */
	{ "><>",      NULL },    /* no layout function means floating behavior */
	{ "[M]",      monocle },
};

/* key definitions */
#define MODKEY Mod1Mask
#define TAGKEYS(KEY,TAG) \
	{ MODKEY,                       KEY,      view,           {.ui = 1 << TAG} }, \
	{ MODKEY|ControlMask,           KEY,      toggleview,     {.ui = 1 << TAG} }, \
	{ MODKEY|ShiftMask,             KEY,      tag,            {.ui = 1 << TAG} }, \
	{ MODKEY|ControlMask|ShiftMask, KEY,      toggletag,      {.ui = 1 << TAG} },

/* helper for spawning shell commands in the pre dwm-5.0 fashion */
#define SHCMD(cmd) { .v = (const char*[]){ "/bin/sh", "-c", cmd, NULL } }

/* commands */
static char dmenumon[2] = "0"; /* component of dmenucmd, manipulated in spawn() */
static const char *dmenucmd[]          = { "dmenu_run", "-m", dmenumon, "-fn", dmenufont, "-nb", col_gray1, "-nf", col_gray3, "-sb", col_gray2, "-sf", col_gray3, NULL };
static const char *termcmd[]           = { "st", NULL };
static const char *torbrowsercmd[]     = { "torbrowser-launcher", NULL };
static const char *firefoxbrowsercmd[] = { "firefox", NULL };
static const char *officecmd[]         = { "libreoffice", NULL };
static const char *lockcmd[]           = { "slock", NULL };

void soundaction(const Arg *arg) {
    syst_sound_mixer_t* sound_mixer = syst_get_sound_mixer(NULL);

    syst_sound_control_list_t* sound_control_list = syst_sound_mixer_get_controls(sound_mixer, NULL);
    unsigned long sound_control_count = syst_sound_control_list_get_size(sound_control_list, NULL);
    for (unsigned long idx = 0; idx < sound_control_count; ++idx) {
        syst_sound_control_t* sound_control = syst_sound_control_list_get(sound_control_list, idx, NULL);
        ((void (*)(syst_sound_control_t*))(arg->v))(sound_control);
    }

    syst_sound_control_list_free(sound_control_list);
    syst_sound_mixer_free(sound_mixer);

    sbar_notify((sbar_top_field_t)(sbar_top_field_audio_playback | sbar_top_field_audio_capture), NULL);
}

void soundplaybackstatustoggle(syst_sound_control_t* sound_control) {
    if (syst_sound_control_has_playback_status(sound_control, NULL)) {
        syst_sound_control_toggle_playback_status(sound_control, NULL);
    }
}

void soundplaybackvolumedown(syst_sound_control_t* sound_control) {
    if (syst_sound_control_has_playback_status(sound_control, NULL)) {
        syst_sound_control_set_playback_volume_all_relative(sound_control, -5, NULL);
    }
}

void soundplaybackvolumeup(syst_sound_control_t* sound_control) {
    if (syst_sound_control_has_playback_status(sound_control, NULL)) {
        syst_sound_control_set_playback_volume_all_relative(sound_control, 5, NULL);
    }
}

void soundcapturestatustoggle(syst_sound_control_t* sound_control) {
    if (syst_sound_control_has_capture_status(sound_control, NULL)) {
        syst_sound_control_toggle_capture_status(sound_control, NULL);
    }
}

void backlightaction(const Arg *arg) {
    syst_backlight_list_t* backlight_list = syst_get_backlights(NULL);
    unsigned long backlight_count = syst_backlight_list_get_size(backlight_list, NULL);
    for (unsigned long idx = 0; idx < backlight_count; ++idx) {
        syst_backlight_t* backlight = syst_backlight_list_get(backlight_list, idx, NULL);
        ((void (*)(syst_backlight_t*))(arg->v))(backlight);
    }

    syst_backlight_list_free(backlight_list);

    sbar_notify(sbar_top_field_backlight, NULL);
}

void backlightdown(syst_backlight_t* backlight) {
    syst_backlight_set_brightness_relative(backlight, -5, NULL);
}

void backlightup(syst_backlight_t* backlight) {
    syst_backlight_set_brightness_relative(backlight, 5, NULL);
}

static const Key keys[] = {
	/* modifier                     key                       function        argument */
	{ MODKEY,                       XK_p,                     spawn,          {.v = dmenucmd } },
	{ MODKEY|ShiftMask,             XK_Return,                spawn,          {.v = termcmd } },
	{ MODKEY|ShiftMask,             XK_o,                     spawn,          {.v = torbrowsercmd } },
	{ MODKEY|ShiftMask,             XK_f,                     spawn,          {.v = firefoxbrowsercmd } },
	{ MODKEY|ShiftMask,             XK_l,                     spawn,          {.v = officecmd } },
	{ MODKEY|ShiftMask,             XK_x,                     spawn,          {.v = lockcmd } },
	{ NoEventMask,                  XF86XK_AudioMute,         soundaction,          {.v = soundplaybackstatustoggle } },
	{ NoEventMask,                  XF86XK_AudioLowerVolume,  soundaction,          {.v = soundplaybackvolumedown } },
	{ NoEventMask,                  XF86XK_AudioRaiseVolume,  soundaction,          {.v = soundplaybackvolumeup } },
	{ NoEventMask,                  XF86XK_AudioMicMute,      soundaction,          {.v = soundcapturestatustoggle } },
	{ NoEventMask,                  XF86XK_MonBrightnessDown, backlightaction,      {.v = backlightdown } },
	{ NoEventMask,                  XF86XK_MonBrightnessUp,   backlightaction,      {.v = backlightup } },
	{ MODKEY,                       XK_b,                     togglebar,      {0} },
	{ MODKEY,                       XK_j,                     focusstack,     {.i = +1 } },
	{ MODKEY,                       XK_k,                     focusstack,     {.i = -1 } },
	{ MODKEY,                       XK_i,                     incnmaster,     {.i = +1 } },
	{ MODKEY,                       XK_d,                     incnmaster,     {.i = -1 } },
	{ MODKEY,                       XK_h,                     setmfact,       {.f = -0.05} },
	{ MODKEY,                       XK_l,                     setmfact,       {.f = +0.05} },
	{ MODKEY,                       XK_Return,                zoom,           {0} },
	{ MODKEY,                       XK_Tab,                   view,           {0} },
	{ MODKEY|ShiftMask,             XK_c,                     killclient,     {0} },
	{ MODKEY,                       XK_t,                     setlayout,      {.v = &layouts[0]} },
	{ MODKEY,                       XK_f,                     setlayout,      {.v = &layouts[1]} },
	{ MODKEY,                       XK_m,                     setlayout,      {.v = &layouts[2]} },
	{ MODKEY,                       XK_space,                 setlayout,      {0} },
	{ MODKEY|ShiftMask,             XK_space,                 togglefloating, {0} },
	{ MODKEY,                       XK_0,                     view,           {.ui = ~0 } },
	{ MODKEY|ShiftMask,             XK_0,                     tag,            {.ui = ~0 } },
	{ MODKEY,                       XK_comma,                 focusmon,       {.i = -1 } },
	{ MODKEY,                       XK_period,                focusmon,       {.i = +1 } },
	{ MODKEY|ShiftMask,             XK_comma,                 tagmon,         {.i = -1 } },
	{ MODKEY|ShiftMask,             XK_period,                tagmon,         {.i = +1 } },
	TAGKEYS(                        XK_1,                                     0)
	TAGKEYS(                        XK_2,                                     1)
	TAGKEYS(                        XK_3,                                     2)
	TAGKEYS(                        XK_4,                                     3)
	TAGKEYS(                        XK_5,                                     4)
	{ MODKEY|ShiftMask,             XK_q,                     quit,           {0} },
};

/* button definitions */
/* click can be ClkTagBar, ClkLtSymbol, ClkStatusText, ClkWinTitle, ClkClientWin, or ClkRootWin */
static const Button buttons[] = {
	/* click                event mask      button          function        argument */
	{ ClkLtSymbol,          0,              Button1,        setlayout,      {0} },
	{ ClkLtSymbol,          0,              Button3,        setlayout,      {.v = &layouts[2]} },
	{ ClkWinTitle,          0,              Button2,        zoom,           {0} },
	{ ClkStatusText,        0,              Button2,        spawn,          {.v = termcmd } },
	{ ClkClientWin,         MODKEY,         Button1,        movemouse,      {0} },
	{ ClkClientWin,         MODKEY,         Button2,        togglefloating, {0} },
	{ ClkClientWin,         MODKEY,         Button3,        resizemouse,    {0} },
	{ ClkTagBar,            0,              Button1,        view,           {0} },
	{ ClkTagBar,            0,              Button3,        toggleview,     {0} },
	{ ClkTagBar,            MODKEY,         Button1,        tag,            {0} },
	{ ClkTagBar,            MODKEY,         Button3,        toggletag,      {0} },
};

