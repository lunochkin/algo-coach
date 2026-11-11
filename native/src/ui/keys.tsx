import { MaterialCommunityIcons } from '@expo/vector-icons';
import { type ReactNode, useEffect, useRef, useState } from 'react';
import { PanResponder, Pressable, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

import {
  afterLetter,
  cased,
  DIGITS,
  dragSteps,
  type Key,
  KEYWORDS,
  keywordText,
  LETTERS,
  RARE,
  RARE_LINES,
  type Shift,
  shiftPressed,
  SYMBOLS,
  WORDS,
} from '@/lib/keys';

const HEIGHT = 40;
const GAP = 5;
const ROWS = 7;
// a held back key repeats, as the system keyboard's does
const REPEAT_MS = 70;

/** The pad's height, for the space a screen leaves under its content. */
export const PAD_HEIGHT = ROWS * HEIGHT + (ROWS - 1) * GAP;

// the layer in the letters' place: the letters, the rare symbols, or the
// keywords an editor adds
type Layer = 'letters' | 'rare' | 'keywords';

// `lines` is the editor's pad: enter where `?` sits, the strip dragging the
// caret, indent and dedent, and the keywords
export function KeyPad({ onKey, lines = false }: { onKey: (key: Key) => void; lines?: boolean }) {
  const [shift, setShift] = useState<Shift>('off');
  const [layer, setLayer] = useState<Layer>('letters');
  const lastShift = useRef(0);
  const repeat = useRef<ReturnType<typeof setInterval> | null>(null);
  const stop = () => {
    if (repeat.current) clearInterval(repeat.current);
    repeat.current = null;
  };
  useEffect(() => stop, []);

  const insert = (text: string) => onKey({ insert: text });
  const letter = (one: string) => {
    insert(cased(one, shift));
    setShift(afterLetter(shift));
  };
  const back = (
    <Cap
      icon="backspace-outline"
      accessibilityLabel="Backspace"
      grow={1.5}
      onPress={() => onKey('back')}
      onLongPress={() => {
        stop();
        repeat.current = setInterval(() => onKey('back'), REPEAT_MS);
      }}
      onPressOut={stop}
    />
  );

  return (
    <View style={{ gap: GAP }}>
      {lines ? (
        <Row>
          <Cap icon="format-indent-decrease" accessibilityLabel="Dedent" onPress={() => onKey('dedent')} />
          <Cap icon="format-indent-increase" accessibilityLabel="Indent" onPress={() => onKey('indent')} />
          {/* a block selected here moves whole under indent and dedent */}
          <Cap icon="select-group" accessibilityLabel="Select the block" onPress={() => onKey('block')} />
          <Strip onKey={onKey} />
          <Cap icon="arrow-up-bold-outline" accessibilityLabel="Move the line up" onPress={() => onKey('lineUp')} />
          <Cap
            icon="arrow-down-bold-outline"
            accessibilityLabel="Move the line down"
            onPress={() => onKey('lineDown')}
          />
          <Cap icon="content-duplicate" accessibilityLabel="Duplicate the line" onPress={() => onKey('duplicate')} />
        </Row>
      ) : null}
      {[...SYMBOLS, DIGITS].map((row) => (
        <Row key={row.join('')}>
          {row.map((one) => (
            <Cap key={one} label={one} preview onPress={() => insert(one)} />
          ))}
        </Row>
      ))}
      {layer === 'keywords' ? (
        <>
          {KEYWORDS.map((row, index) => (
            <Row key={row.join('')}>
              {row.map((one) => (
                <Cap
                  key={one}
                  label={one}
                  onPress={() => {
                    insert(keywordText(one));
                    // one keyword at a time: a name follows it, typed in letters
                    setLayer('letters');
                  }}
                />
              ))}
              {index === KEYWORDS.length - 1 ? back : null}
            </Row>
          ))}
        </>
      ) : layer === 'rare' ? (
        <>
          <Row>
            {(lines ? RARE_LINES : RARE).map((one) => (
              <Cap key={one} label={one} preview onPress={() => insert(one)} />
            ))}
          </Row>
          <Row>
            {WORDS.map((one) => (
              <Cap key={one} label={one} onPress={() => insert(one)} />
            ))}
          </Row>
          <Row>
            <View style={{ flex: 8.5 }} />
            {back}
          </Row>
        </>
      ) : (
        <>
          <Row>
            {LETTERS[0].map((one) => (
              <Cap key={one} label={cased(one, shift)} preview onPress={() => letter(one)} />
            ))}
          </Row>
          <Row>
            {LETTERS[1].map((one) => (
              <Cap key={one} label={cased(one, shift)} preview onPress={() => letter(one)} />
            ))}
          </Row>
          <Row>
            <Cap
              icon={shift === 'lock' ? 'apple-keyboard-caps' : 'apple-keyboard-shift'}
              accessibilityLabel="Shift"
              grow={1.5}
              on={shift !== 'off'}
              onPress={() => {
                const now = Date.now();
                setShift(shiftPressed(shift, now - lastShift.current));
                lastShift.current = now;
              }}
            />
            {LETTERS[2].map((one) => (
              <Cap key={one} label={cased(one, shift)} preview onPress={() => letter(one)} />
            ))}
            {back}
          </Row>
        </>
      )}
      <Row>
        <Cap
          label={layer === 'rare' ? 'abc' : '#@'}
          accessibilityLabel={layer === 'rare' ? 'Letters' : 'More symbols'}
          grow={1.5}
          onPress={() => setLayer(layer === 'rare' ? 'letters' : 'rare')}
        />
        {lines ? (
          <Cap
            label={layer === 'keywords' ? 'abc' : 'def'}
            accessibilityLabel={layer === 'keywords' ? 'Letters' : 'Keywords'}
            grow={1.5}
            on={layer === 'keywords'}
            onPress={() => setLayer(layer === 'keywords' ? 'letters' : 'keywords')}
          />
        ) : null}
        <Cap label="," preview onPress={() => insert(',')} />
        <Cap icon="chevron-left" accessibilityLabel="Cursor left" onPress={() => onKey('left')} />
        <Cap label="space" grow={lines ? 2 : 3.5} accessibilityLabel="Space" onPress={() => insert(' ')} />
        <Cap icon="chevron-right" accessibilityLabel="Cursor right" onPress={() => onKey('right')} />
        {lines ? (
          <Cap icon="keyboard-return" accessibilityLabel="Enter" onPress={() => onKey('enter')} />
        ) : (
          <Cap label="?" preview onPress={() => insert('?')} />
        )}
      </Row>
    </View>
  );
}

// a bar the finger drags to move the caret: a character per stride sideways,
// a line per stride up or down. Tapping between characters on a phone lands
// a character or two off
function Strip({ onKey }: { onKey: (key: Key) => void }) {
  const theme = useTheme();
  const [held, setHeld] = useState(false);
  const made = useRef({ x: 0, y: 0 });
  const sink = useRef(onKey);
  sink.current = onKey;
  const pan = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderGrant: () => {
        made.current = { x: 0, y: 0 };
        setHeld(true);
      },
      onPanResponderMove: (_, drag) => {
        const steps = dragSteps(drag.dx, drag.dy);
        for (; made.current.x < steps.x; made.current.x++) sink.current('right');
        for (; made.current.x > steps.x; made.current.x--) sink.current('left');
        for (; made.current.y < steps.y; made.current.y++) sink.current('down');
        for (; made.current.y > steps.y; made.current.y--) sink.current('up');
      },
      onPanResponderRelease: () => setHeld(false),
      onPanResponderTerminate: () => setHeld(false),
    }),
  ).current;
  return (
    <View
      {...pan.panHandlers}
      accessibilityLabel="Drag to move the cursor"
      style={{
        flex: 3,
        height: HEIGHT,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: held ? theme.colors.surfaceDisabled : theme.colors.elevation.level3,
      }}
    >
      <MaterialCommunityIcons name="cursor-move" size={20} color={theme.colors.onSurfaceVariant} />
    </View>
  );
}

const Row = ({ children }: { children: ReactNode }) => (
  <View style={{ flexDirection: 'row', gap: GAP }}>{children}</View>
);

function Cap(props: {
  label?: string;
  icon?: keyof typeof MaterialCommunityIcons.glyphMap;
  accessibilityLabel?: string;
  grow?: number;
  // shown above the finger while pressed: a key is narrower than the finger on it
  preview?: boolean;
  on?: boolean;
  onPress: () => void;
  onLongPress?: () => void;
  onPressOut?: () => void;
}) {
  const theme = useTheme();
  const { label, icon, grow = 1, preview = false, on = false } = props;
  const ink = on ? theme.colors.onPrimary : theme.colors.onSurfaceVariant;
  const ground = on ? theme.colors.primary : theme.colors.surfaceVariant;
  let face: ReactNode = null;
  if (icon) face = <MaterialCommunityIcons name={icon} size={20} color={ink} />;
  else if (label)
    face = (
      // a keyword shrinks to its key rather than wrapping inside it
      <Text
        numberOfLines={1}
        adjustsFontSizeToFit
        minimumFontScale={0.6}
        style={{ fontFamily: 'monospace', fontSize: label.length > 1 ? 13 : 18, color: ink, paddingHorizontal: 2 }}
      >
        {label}
      </Text>
    );
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={props.accessibilityLabel ?? label}
      onPress={props.onPress}
      onLongPress={props.onLongPress}
      onPressOut={props.onPressOut}
      delayLongPress={350}
      style={({ pressed }) => ({
        flex: grow,
        height: HEIGHT,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: pressed ? theme.colors.surfaceDisabled : ground,
      })}
    >
      {({ pressed }) => (
        <>
          {face}
          {pressed && preview && label ? (
            <View
              pointerEvents="none"
              style={{
                position: 'absolute',
                bottom: HEIGHT + 4,
                minWidth: '120%',
                height: HEIGHT + 8,
                borderRadius: 8,
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: theme.colors.inverseSurface,
                elevation: 4,
              }}
            >
              <Text style={{ fontFamily: 'monospace', fontSize: 24, color: theme.colors.inverseOnSurface }}>
                {label}
              </Text>
            </View>
          ) : null}
        </>
      )}
    </Pressable>
  );
}
