import com.googlecode.lanterna.Symbols
import com.googlecode.lanterna.TextCharacter
import com.googlecode.lanterna.TextColor
import com.googlecode.lanterna.screen.TerminalScreen
import java.lang.RuntimeException

fun TerminalScreen.drawMap(state: Map, curPlayer: String, curState: State) {
    this.clear()
    for (wall in state.walls) {
        this.setCharacter(wall[0], wall[1], TextCharacter.fromCharacter('#')[0])
    }
    for (enemy in state.enemies) {
        val icon = when (enemy.kind) {
            "agr_enemy" -> TextCharacter.fromCharacter('E', TextColor.ANSI.RED, TextColor.ANSI.DEFAULT)[0]
            "passive_enemy" -> TextCharacter.fromCharacter('P', TextColor.ANSI.BLUE, TextColor.ANSI.DEFAULT)[0]
            else -> throw RuntimeException("unknown enemy type")
        }
        this.setCharacter(enemy.curPos[0], enemy.curPos[1], icon)
    }
    this.setCharacter(state.stairs[0], state.stairs[1], TextCharacter.fromCharacter('>')[0])
    var health = 0
    val myColor = if (curState == State.ACTIVE) {
        TextColor.ANSI.GREEN
    } else {
        TextColor.ANSI.YELLOW
    }
    for (player in state.players) {
        val icon = when (player.userId) {
            curPlayer -> {
                health = player.health;
                TextCharacter.fromCharacter('@', myColor, TextColor.ANSI.DEFAULT)[0]
            }
            else -> TextCharacter.fromCharacter('@')[0]
        }
        this.setCharacter(player.curPos[0], player.curPos[1], icon)
    }
    val healthGraphics = this.newTextGraphics()
    healthGraphics.drawLine(0, 20, 19, 20, Symbols.DOUBLE_LINE_HORIZONTAL)
    healthGraphics.putString(0, 21, "Health: $health")
    this.refresh()
}