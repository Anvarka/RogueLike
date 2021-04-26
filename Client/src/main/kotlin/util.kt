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
data class Map(val walls: List<List<Int>>,
               val player: Character,
               val stairs: List<Int>,
               val enemies: List<Character>,
               @SerialName("game_over") val gameOver: Boolean)

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
