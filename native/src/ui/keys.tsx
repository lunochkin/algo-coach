import { MaterialCommunityIcons } from '@expo/vector-icons';
import { type ReactNode, useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

import {
  afterLetter,
  cased,
  DIGITS,
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

// `lines` is the editor's pad: enter where `?` sits, the line keys, the
// names the file declares, and the keywords
export function KeyPad({
  onKey,
  lines = false,
  names = [],
}: {
  onKey: (key: Key) => void;
  lines?: boolean;
  names?: string[];
}) {
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
          <Cap grow={0.75} icon="format-indent-decrease" accessibilityLabel="Dedent" onPress={() => onKey('dedent')} />
          <Cap grow={0.75} icon="format-indent-increase" accessibilityLabel="Indent" onPress={() => onKey('indent')} />
          {/* a block selected here moves whole under indent and dedent */}
          <Cap grow={0.75} icon="select-group" accessibilityLabel="Select the block" onPress={() => onKey('block')} />
          <Names names={names} onKey={onKey} />
          <Cap
            grow={0.75}
            icon="arrow-up-bold-outline"
            accessibilityLabel="Move the line up"
            onPress={() => onKey('lineUp')}
          />
          <Cap
            grow={0.75}
            icon="arrow-down-bold-outline"
            accessibilityLabel="Move the line down"
            onPress={() => onKey('lineDown')}
          />
          <Cap
            grow={0.75}
            icon="content-duplicate"
            accessibilityLabel="Duplicate the line"
            onPress={() => onKey('duplicate')}
          />
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

// the names the file declares, in the strip's place so they cost no height:
// `flows.md` gives why a declared name is offered and a library name never is
function Names({ names, onKey }: { names: string[]; onKey: (key: Key) => void }) {
  const theme = useTheme();
  return (
    // a horizontal scroll sizes to its content inside a row, so a plain view
    // holds the row's share and the scroll fills it
    <View style={{ flex: 5, height: HEIGHT, borderRadius: 8, backgroundColor: theme.colors.elevation.level3 }}>
      <ScrollView
        horizontal
        keyboardShouldPersistTaps="always"
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ alignItems: 'center', gap: GAP, paddingHorizontal: 4 }}
      >
        {names.map((one) => (
          <Pressable
            key={one}
            accessibilityRole="button"
            accessibilityLabel={`Name ${one}`}
            onPress={() => onKey({ name: one })}
            style={({ pressed }) => ({
              height: HEIGHT - 8,
              paddingHorizontal: 10,
              borderRadius: 6,
              justifyContent: 'center',
              backgroundColor: pressed ? theme.colors.surfaceDisabled : theme.colors.surfaceVariant,
            })}
          >
            <Text style={{ fontFamily: 'monospace', fontSize: 14, color: theme.colors.onSurfaceVariant }}>{one}</Text>
          </Pressable>
        ))}
      </ScrollView>
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
