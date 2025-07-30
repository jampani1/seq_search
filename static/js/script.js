//Se houver um arquivo selecionado, exibe o nome do arquivo
function mostrarNomeArquivo() {
    const input = document.getElementById('arquivo');
    const span = document.getElementById('nome-arquivo');
    if (input.files.length > 0) {
        span.textContent = input.files[0].name;
    } else {
        span.textContent = "Nenhum arquivo selecionado";
    }
}

//Controla o envio do formulário
// Se o botão "search" for clicado, verifica se a sequência ou o arquivo estão preenchida
// Se nenhum dos dois estiver preenchido, cancela o envio e exibe um alerta
document.addEventListener('DOMContentLoaded', function () {
    const formulario = document.getElementById('formulario');

    formulario.addEventListener('submit', function (event) {
        const sequencia = document.querySelector('textarea[name="sequencia"]').value.trim();
        const arquivo = document.querySelector('input[type="file"]').files[0];
        const efetor = document.querySelector('input[name="efetor"]').value.trim();
        const action = event.submitter?.value; // "search"

        if (action === "search") {
            if (!sequencia && !arquivo) {
                event.preventDefault();
                alert("You need to input a valid sequence or upload a .fasta file.");
                return;
            }

            if (!efetor) {
                event.preventDefault();
                alert("Insert a valid effector.");
                return;
            }
        }
    });
});

//Faz com que a mensagem de erro desapareça após clicar em qualquer lugar da página
document.addEventListener('click', function () {
    const mensagem = document.getElementById('mensagem-flash');
    if (mensagem) {
        mensagem.style.display = 'none';
    }
});
