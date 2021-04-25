import com.googlecode.lanterna.TextCharacter
import com.googlecode.lanterna.TextColor
import com.googlecode.lanterna.screen.TerminalScreen
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import java.lang.RuntimeException

// Types for serialization


@Serializable
data class Character(val kind: String, val health: Int, @SerialName("cur_pos") val curPos: List<Int>)

@Serializable
data class Map(val walls: List<List<Int>>, val player: Character, val stairs: List<Int>, val enemies: List<Character>) {
    fun draw(screen: TerminalScreen) {
        screen.clear()
        for (wall in walls) {
            screen.setCharacter(wall[0], wall[1], TextCharacter.fromCharacter('#')[0])
        }
        for (enemy in enemies) {
            val icon = when (enemy.kind) {
                "agr_enemy" -> TextCharacter.fromCharacter('E', TextColor.ANSI.RED, TextColor.ANSI.DEFAULT)[0]
                "pas_enemy" -> TextCharacter.fromCharacter('P', TextColor.ANSI.BLUE, TextColor.ANSI.DEFAULT)[0]
                else -> throw RuntimeException("unknown enemy type")
            }
            screen.setCharacter(enemy.curPos[0], enemy.curPos[1], icon)
        }
        screen.setCharacter(stairs[0], stairs[1], TextCharacter.fromCharacter('>')[0])
        screen.setCharacter(player.curPos[0], player.curPos[1], TextCharacter.fromCharacter('@')[0])
        screen.refresh()
    }
}

@Serializable
data class UserId(@SerialName("user_id") val userId: String)

@Serializable
enum class Direction {
    @SerialName("up") UP,
    @SerialName("down") DOWN,
    @SerialName("left") LEFT,
    @SerialName("right") RIGHT
}

@Serializable
data class MoveRequest(val user_id: String, val direction: Direction)
